"""支付模块后台管理。"""

from django.contrib import admin

from .models import PaymentRecord


@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ["payment_no", "order", "amount", "status", "paid_at", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["payment_no", "order__order_no"]
    date_hierarchy = "created_at"
