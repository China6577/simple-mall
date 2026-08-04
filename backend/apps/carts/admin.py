"""购物车模块后台管理。"""

from django.contrib import admin

from .models import CartItem


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "sku", "quantity", "selected", "created_at"]
    list_filter = ["selected", "created_at"]
    search_fields = ["user__username", "sku__sku_code", "sku__spu__name"]
    date_hierarchy = "created_at"
