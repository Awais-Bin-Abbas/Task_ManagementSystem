from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User


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
    
