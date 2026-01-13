from django.contrib import admin
from .models import OrderItem, Order, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'tag', 'created_at')
    list_filter = ('category', 'tag', 'created_at')
    
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity', 'price')
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__email', 'id', 'paystack_reference')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)