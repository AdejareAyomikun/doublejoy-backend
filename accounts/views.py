# accounts/views.py
from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from django.conf import settings

class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
