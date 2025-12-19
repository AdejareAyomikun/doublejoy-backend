from rest_framework import viewsets, status
from rest_framework.permissions import SAFE_METHODS, BasePermission, AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Product, Category, Cart, CartItem
from .serializers import ProductSerializer, CategorySerializer, CartSerializer
from .permissions import IsAdminOrReadOnly


class CartViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_cart(self, user):
        cart, _ = Cart.objects.get_or_create(user=user)
        return cart

    def list(self, request):
        cart = self.get_cart(request.user)
        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data)

    def create(self, request):
        cart = self.get_cart(request.user)

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

        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product
        )
        if created:
            item.quantity = max(1, quantity)
        else:
            item.quantity = max(1, item.quantity + quantity)

        item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def update_quantity(self, request):
        cart = self.get_cart(request.user)
        item_id = request.data.get("item_id")
        action_type = request.data.get("action")

        if not item_id or action_type not in ["increment", "decrement"]:
            return Response(
                {"error": "item_id and valid action are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = CartItem.objects.get(id=item_id, cart=cart)
        except CartItem.DoesNotExist:
            return Response(
                {"error": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if action_type == "increment":
            item.quantity += 1
            item.save()
        elif action_type == "decrement":
            item.quantity -= 1
            if item.quantity <= 0:
                item.delete()
            else:
                item.save()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


    @action(detail=False, methods=["post"])
    def remove_item(self, request):
        cart = self.get_cart(request.user)
        item_id = request.data.get("item_id")

        if not item_id:
            return Response(
                {"error": "item_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        CartItem.objects.filter(id=item_id, cart=cart).delete()

        serializer = CartSerializer(cart, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def clear(self, request):
        cart = self.get_cart(request.user)
        cart.items.all().delete()
        return Response({"message": "Cart cleared"}, status=status.HTTP_200_OK)


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
