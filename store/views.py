import uuid
from rest_framework.views import APIView
from rest_framework import viewsets, permissions, status
from .permissions import IsAdminOrReadOnly
from rest_framework.permissions import SAFE_METHODS, BasePermission, AllowAny
from .models import Product, Category, CartItem
from .serializers import ProductSerializer, CategorySerializer, CartItemSerializer
from .permissions import IsAdminOrReadOnly
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response


class CartViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def _get_session_id(self, request):
        session_id = request.COOKIES.get("session_id")
        if not session_id:
            session_id = str(uuid.uuid4())
        return session_id

    def list(self, request):
        session_id = self._get_session_id(request)
        items = CartItem.objects.filter(session_id=session_id)
        serializer = CartItemSerializer(items, many=True)

        response = Response(serializer.data)
        response.set_cookie("session_id", session_id)
        return response

    def create(self, request):
        session_id = self._get_session_id(request)

        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"error": "product_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        cart_item, created = CartItem.objects.get_or_create(
            session_id=session_id,
            product=product,
            defaults={"quantity": quantity}
        )

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        response = Response(
            CartItemSerializer(cart_item).data,
            status=status.HTTP_201_CREATED
        )
        response.set_cookie("session_id", session_id)
        return response


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrReadOnly]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        self.perform_create(serializer)
        return Response(serializer.data, status=201)


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
