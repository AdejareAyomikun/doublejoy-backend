from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAdminUser
from django.utils.timezone import now
from django.db.models import Sum
from store.services.order_analytics import (
    daily_sales,
    best_selling_products,
)

from store.models import Order, OrderItem


class AdminDashboardAnalytics(APIView):
    authentication_classes = [
        JWTAuthentication,
    ]
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = now().date()

        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status__in=["pending", "shipped"]).count()
        completed_orders = Order.objects.filter(status__in=["delivered", "completed", "cancelled"]).count()

        total_revenue = Order.objects.filter(status__in=["paid", "delivered", "shipped", "completed"]).aggregate(
            total=Sum("total_amount")
        )["total"] or 0,

        print("User:", request.user)
        print("Authenticated:", request.user.is_authenticated)
        print("Is staff:", getattr(request.user, "is_staff", None))
        
        
        return Response({
            "summary": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "completed_orders": completed_orders,
                "total_revenue": total_revenue,
            },
            "daily_sales": daily_sales(7),
            "top_products": best_selling_products(5),
        })
