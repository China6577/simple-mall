"""订单模块后台管理。"""

from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ["sku", "sku_code", "spu_name", "specs", "price", "quantity", "subtotal"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_no", "user", "status", "payable_amount", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_no", "user__username"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "spu_name", "sku_code", "price", "quantity", "subtotal"]
    search_fields = ["order__order_no", "spu_name", "sku_code"]
