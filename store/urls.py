from django.urls import path
from rest_framework import routers
from .views import ProductViewSet, CategoryViewSet, CartViewSet

router = routers.DefaultRouter()
router.register(r'products', ProductViewSet)
router.register(r"categories", CategoryViewSet)
router.register(r"cart", CartViewSet, basename="cart")

urlpatterns = router.urls