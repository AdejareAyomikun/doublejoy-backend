from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class DebugJWTView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]  # IMPORTANT

    def get(self, request):
        auth_header = request.headers.get("Authorization")

        try:
            user_auth_tuple = JWTAuthentication().authenticate(request)
        except AuthenticationFailed as e:
            return Response({
                "error": "AuthenticationFailed",
                "detail": str(e),
                "auth_header": auth_header,
            }, status=401)

        if user_auth_tuple is None:
            return Response({
                "error": "No authentication",
                "auth_header": auth_header,
            }, status=401)

        user, token = user_auth_tuple

        return Response({
            "authenticated": True,
            "user_id": user.id,
            "username": user.username,
            "is_staff": user.is_staff,
            "token_payload": token.payload,
        })
