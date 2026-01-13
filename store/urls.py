from django.urls import path, include
from rest_framework import routers
from .views import ProductViewSet, CategoryViewSet, CartViewSet, OrderViewSet

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"cart", CartViewSet, basename="cart")
router.register(r"orders", OrderViewSet, basename="orders")

urlpatterns = router.urls
