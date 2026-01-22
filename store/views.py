import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
from django.db.models import Sum, Avg
from rest_framework import viewsets, status, permissions, authentication
from rest_framework.permissions import SAFE_METHODS, BasePermission, IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response

from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .serializers import ProductSerializer, CategorySerializer, CartSerializer, OrderSerializer
from .permissions import IsAdminOrReadOnly,  PublicReadAdminWrite

from paystackapi.transaction import Transaction
from django.utils import timezone
import json

DELIVERY_FEES = {
    "lagos": 5000,
    "ogun": 8000,
    "oyo": 8000,
}


class OrderViewSet(viewsets.ModelViewSet):
    # queryset = Order.objects.all().order_by('-created_at')
    # serializer_class = OrderSerializer
    # permission_classes = [IsAdminUser]

    serializer_class = OrderSerializer
    print("🔥 LOADED OrderViewSet from:", __file__)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        qs = Order.objects.all().order_by("-created_at")
        if self.request.user.is_staff:
            return qs
        return qs.filter(user=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        status_value = request.data.get("status")

        if status_value:
            order.status = status_value
            order.save()

        serializer = self.get_serializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        cart = self.get_cart(request.user)

        if not cart.items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        address = request.data.get("address")
        city = request.data.get("city")
        state = request.data.get("state")

        if not all([address, city, state]):
            return Response(
                {"error": "Address, City and State are required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        state_key = state.lower()

        if state_key not in DELIVERY_FEES:
            return Response(
                {"error": "Delivery is only available in Lagos, Ogun and Oyo"},
                status=status.HTTP_400_BAD_REQUEST
            )

        cart_total = sum(
            item.product.price * item.quantity for item in cart.items.all()
        )

        delivery_fee = DELIVERY_FEES[state_key]

        total_amount = cart_total + delivery_fee

        order = Order.objects.create(
            user=request.user,
            total_amount=total_amount,
            delivery_fee=delivery_fee,
            address=address,
            city=city,
            state=state,
            status="pending"
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.price
            )

        paystack_amount = int(total_amount * 100)  # amount in kobo

        response = Transaction.initialize(
            reference=f"Order-{order.id}",
            amount=paystack_amount,
            email=request.user.email or "test@example.com",
            callback_url="http://localhost:3000/payment/success",
            secret_key=settings.PAYSTACK_SECRET_KEY,
        )
        order.paystack_reference = response["data"]["reference"]
        order.save()

        cart.items.all().delete()  # clear cart after checkout

        if not response.get("status"):
            return Response(
                {
                    "error": "Payment initialization failed",
                    "message": response.get("message"),
                },
                status=400,
            )

        return Response({
            "payment_url": response["data"]["authorization_url"],
            "reference": response["data"]["reference"],
            "order_id": order.id
        }, status=200)

    @action(detail=False, methods=["get"])
    def verify_payment(self, request):
        reference = request.query_params.get("reference")

        if not reference:
            return Response({"error": "Reference is required"}, status=400)

        response = Transaction.verify(
            reference=reference
        )

        if response["data"]["status"] == "success":
            order = Order.objects.get(paystack_reference=reference)
            order.status = "paid"
            order.paid_at = timezone.now()
            order.save()

            return Response({
                "message": "Payment verified",
                "order_id": order.id
            })

        return Response({"error": "Payment verification failed"}, status=400)

    @action(detail=False, methods=["post"])
    def paystack_init(self, request):
        order_id = request.data.get("order_id")

        try:
            order = Order.objects.get(id=order_id, user=request.user)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        response = Transaction.initialize(
            email=request.user.email,
            amount=int(order.total_amount * 100),  # amount in kobo
            reference=f"ORDER-{order.id}"
        )
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def paystack_verify(self, request):
        reference = request.data.get("reference")

        if not reference:
            return Response(
                {"error": "Payment reference is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        response = Transaction.verify(reference=reference)

        if response['data']['status'] == 'success':
            order_id = reference.replace("ORDER_", "")

            try:
                order = Order.objects.get(id=order_id)
                order.status = "paid"
                order.save()
            except Order.DoesNotExist:
                pass

            return Response(
                {"message": "Payment verified successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Payment verification failed"},
            status=status.HTTP_400_BAD_REQUEST
        )


@csrf_exempt
def paystack_webhook(request):
    paystack_signature = request.headers.get("x-paystack-signature")

    computed_signature = hashlib.sha512(
        request.body + settings.PAYSTACK_SECRET_KEY.encode()
    ).hexdigest()

    if computed_signature != paystack_signature:
        return HttpResponse(status=401)

    payload = json.loads(request.body)

    if payload["event"] == "charge.success":
        reference = payload["data"]["reference"]

        try:
            order = Order.objects.get(paystack_reference=reference)
            order.status = "paid"
            order.paid_at = timezone.now()
            order.save()
        except Order.DoesNotExist:
            pass

    return HttpResponse(status=200)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    authentication_classes = [
        JWTAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    ]
    permission_classes = [PublicReadAdminWrite]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    authentication_classes = [
        JWTAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    ]

    permission_classes = [PublicReadAdminWrite]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        queryset = Product.objects.all()

        category_id = self.request.query_params.get("category")
        tag = self.request.query_params.get("tag")
        if category_id:
            queryset = queryset.filter(category_id=category_id)

        if tag == "best_seller":
            queryset = queryset.annotate(
                total_sold=Sum("items__quantity")
            ).order_by("-total_sold")

        elif tag == "top_rated":
            queryset = queryset.annotate(
                avg_rating=Avg("reviews__rating")
            ).order_by("-avg_rating")

        elif tag:
            queryset = queryset.filter(tags=tag)

        return queryset

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("❌ SERIALIZER ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    def update(self, request, *args, **kwargs):
        partial = True  # 🔑 allow partial updates
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )

        if not serializer.is_valid():
            print("❌ UPDATE ERRORS:", serializer.errors)
            return Response(serializer.errors, status=400)

        self.perform_update(serializer)
        return Response(serializer.data)
