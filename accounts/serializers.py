from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    admin_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password",
                  "first_name", "last_name", "admin_key")
        read_only_fields = ("id",)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        admin_key = validated_data.pop("admin_key", "")
        password = validated_data.pop("password")
        is_staff = False

        from django.conf import settings
        secret = getattr(settings, "ADMIN_REGISTRATION_KEY", None)
        if secret and admin_key and admin_key == secret:
            is_staff = True

        user = User(**validated_data)
        user.is_staff = is_staff
        user.set_password(password)
        user.save()
        return user


class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["is_staff"] = user.is_staff
        token["username"] = user.username
        return token
