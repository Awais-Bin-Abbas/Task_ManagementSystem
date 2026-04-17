# accounts/views.py

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import User, PasswordResetRequest
from .serializers import (
    UserSerializer, 
    RegisterSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ChangePasswordSerializer,
    PasswordResetRequestSerializer,
    ResolvePasswordRequestSerializer
)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

class UserAPIView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    @extend_schema(
        summary="Create a new user",
        description="Only a Manager can create new users. Requires JWT authentication.",
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiExample("Invalid data", value={"error": "Invalid data!"}),
            401: OpenApiExample("Unauthorized", value={"error": "Only Manager can create users"}),
        },
        examples=[
            OpenApiExample(
                "Create Member Example",
                value={
                    "username": "Allen",
                    "email": "allen@example.com",
                    "password": "StrongPass123!",
                    "role": "Member",
                    "team": 1
                },
                request_only=True,
            )
        ],
        tags=["Users"]
    )
    def post(self, request):
        user = request.user
        if user.role == 'Manager':
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response({"error": "Only Manager can create users"}, status=status.HTTP_401_UNAUTHORIZED)

    @extend_schema(
        summary="Get all users or a single user",
        description="Returns a list of all users. Pass `id` as a query param to get a single user.",
        parameters=[
            OpenApiParameter(
                name="id",
                description="ID of the user to retrieve",
                required=False,
                type=int
            )
        ],
        responses={
            200: UserSerializer(many=True),
            404: OpenApiExample("Not found", value={"error": "User not found"}),
        },
        tags=["Users"]
    )
    def get(self, request):
        user_id = request.query_params.get("id")
        if user_id:
            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.serializer_class(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Partially update a user",
        description="Update one or more fields of a user. Pass `id` in the request body.",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiExample("Bad request", value={"error": "User id required"}),
            404: OpenApiExample("Not found", value={"error": "User not found"}),
        },
        tags=["Users"]
    )
    def patch(self, request):
        user_id = request.data.get("id")
        if not user_id:
            return Response({"error": "User id required"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=user_id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete a user",
        description="Delete a user by their ID passed as a URL parameter.",
        responses={
            200: OpenApiExample("Success", value={"success": "User deleted successfully"}),
            400: OpenApiExample("Bad request", value={"error": "User id required"}),
            404: OpenApiExample("Not found", value={"error": "User not found"}),
        },
        tags=["Users"]
    )
    def delete(self, request, id=None):
        if not id:
            return Response({"error": "User id required"}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.filter(id=id).first()
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"success": "User deleted successfully"}, status=status.HTTP_200_OK)


class ForgotPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            user = User.objects.filter(username=username).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Create a PasswordResetRequest entry in the database
            PasswordResetRequest.objects.create(user=user, is_resolved=False)
            
            return Response({"success": "If the user exists, your request has been sent to the Manager for approval."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            user = User.objects.filter(username=username).first()
            if not user:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            token_generator = PasswordResetTokenGenerator()
            if not token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.password_expires_at = timezone.now() + timedelta(hours=24)
            user.save()
            
            if user.email:
                send_mail(
                    subject="Your Password Has Been Reset",
                    message=f"Your manager has reset your password. Your new temporary password is: {new_password}\nThis temporary password will expire in 24 hours. Please log in and update your password immediately.",
                    from_email="noreply@taskmanager.local",
                    recipient_list=[user.email],
                    fail_silently=True,
                )
            
            return Response({"success": "Password has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']
            
            user = request.user
            if not user.check_password(old_password):
                return Response({"error": "Old password is not correct"}, status=status.HTTP_400_BAD_REQUEST)
                
            user.set_password(new_password)
            user.password_expires_at = None
            user.save()
            
            return Response({"success": "Password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordRequestsView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'Manager':
            return Response({"error": "Only Managers can view password reset requests."}, status=status.HTTP_403_FORBIDDEN)
        
        requests = PasswordResetRequest.objects.filter(is_resolved=False)
        serializer = PasswordResetRequestSerializer(requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ResolvePasswordRequestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'Manager':
            return Response({"error": "Only Managers can resolve password reset requests."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ResolvePasswordRequestSerializer(data=request.data)
        if serializer.is_valid():
            request_id = serializer.validated_data['request_id']
            new_password = serializer.validated_data['new_password']
            
            # Use a very specific name for the target user object and fetch it freshly
            reset_request = PasswordResetRequest.objects.filter(id=request_id, is_resolved=False).first()
            if not reset_request:
                return Response({"error": "Active password reset request not found"}, status=status.HTTP_404_NOT_FOUND)
            
            # Fetch a fresh instance of the specific user to be updated
            target_user = User.objects.get(id=reset_request.user_id)
            
            # Explicitly update the target_user object ONLY
            target_user.set_password(new_password)
            target_user.password_expires_at = timezone.now() + timedelta(seconds=30)
            target_user.save()
            
            # Update the request status
            reset_request.is_resolved = True
            reset_request.save()
            
            if target_user.email:
                send_mail(
                    subject="Your Password Has Been Reset",
                    message=f"Your manager has reset your password. Your new temporary password is: {new_password}\nThis temporary password will expire in 24 hours. Please log in and update your password immediately.",
                    from_email="noreply@taskmanager.local",
                    recipient_list=[target_user.email],
                    fail_silently=True,
                )
            
            return Response({"success": f"Password for {target_user.username} has been reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)