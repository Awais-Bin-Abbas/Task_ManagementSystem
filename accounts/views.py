# accounts/views.py

from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework import views, status, permissions
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer, RegisterSerializer


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