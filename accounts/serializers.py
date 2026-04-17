from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, PasswordResetRequest


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role, username, and user_id to the JWT access token payload."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Custom claims
        token['role'] = user.role
        token['username'] = user.username
        token['user_id'] = user.id
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        from django.utils import timezone
        from rest_framework.exceptions import AuthenticationFailed
        if self.user.password_expires_at and self.user.password_expires_at < timezone.now():
            raise AuthenticationFailed("Password has expired. Please request a new password reset from your manager.")
        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'role',
            'team',
            'date_joined'
        ]


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'role',
            'team'
        ]

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role'],
            team=validated_data.get('team')
        )

        return user


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()


class ResetPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PasswordResetRequest
        fields = ['id', 'username', 'requested_at']


class ResolvePasswordRequestSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()
    new_password = serializers.CharField(write_only=True)
