from django.urls import path, include
from rest_framework import routers
from .views import ProductViewSet, CategoryViewSet, CartViewSet, OrderViewSet, paystack_webhook
from store.api.admin_analytics_views import AdminDashboardAnalytics

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = [
    path("", include(router.urls)),
    path("paystack/webhook/", paystack_webhook),
    path("admin/analytics/", AdminDashboardAnalytics.as_view()),
]
