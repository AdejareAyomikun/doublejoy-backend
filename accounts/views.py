from rest_framework import generics, permissions
from .serializers import RegisterSerializer, CustomTokenSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.conf import settings


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
