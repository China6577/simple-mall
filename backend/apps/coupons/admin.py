"""优惠券模块后台管理。"""

from django.contrib import admin

from .models import Coupon, OrderCoupon, UserCoupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        "code",
        "name",
        "type",
        "value",
        "min_order_amount",
        "remaining_quantity",
        "limit_per_user",
        "start_time",
        "end_time",
        "is_active",
    ]
    list_filter = ["type", "is_active"]
    search_fields = ["code", "name"]


@admin.register(UserCoupon)
class UserCouponAdmin(admin.ModelAdmin):
    list_display = ["user", "coupon", "status", "claimed_at", "used_at"]
    list_filter = ["status"]
    search_fields = ["user__username", "coupon__name"]


@admin.register(OrderCoupon)
class OrderCouponAdmin(admin.ModelAdmin):
    list_display = ["order", "user_coupon", "discount_amount"]
    search_fields = ["order__order_no"]
