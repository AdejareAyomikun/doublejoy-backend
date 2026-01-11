from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from store.models import Order, OrderItem


def sales_summary():
    return {
        "total_orders": Order.objects.count(),
        "total_revenue": Order.objects.filter(status="paid").aggregate(
            total=Sum("total_amount")
        )["total"] or 0,
        "pending_orders": Order.objects.filter(status="pending").count(),
        "completed_orders": Order.objects.filter(status="delivered").count(),
    }


def daily_sales(days=7):
    start_date = timezone.now() - timedelta(days=days)
    return (
        Order.objects.filter(status="paid", created_at__gte=start_date)
        .extra({"day": "date(created_at)"})
        .values("day")
        .annotate(total=Sum("total_amount"), orders=Count("id"))
        .order_by("day")
    )


def best_selling_products(limit=5):
    return (
        OrderItem.objects.filter(order__status="paid")
        .values("product__name")
        .annotate(
            quantity_sold=Sum("quantity"),
            revenue=Sum("price"),
        )
        .order_by("-quantity_sold")[:limit]
    )
