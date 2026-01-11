from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAdminUser
from store.services.order_analytics import (
    sales_summary,
    daily_sales,
    best_selling_products,
)


class AdminDashboardAnalytics(APIView):
    authentication_classes = [
        JWTAuthentication,
    ]
    permission_classes = [IsAdminUser]

    def get(self, request):
        print("User:", request.user)
        print("Authenticated:", request.user.is_authenticated)
        print("Is staff:", getattr(request.user, "is_staff", None))
        return Response({
            "summary": sales_summary(),
            "daily_sales": daily_sales(7),
            "top_products": best_selling_products(5),
        })
