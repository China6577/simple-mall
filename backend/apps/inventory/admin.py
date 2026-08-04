"""库存模块 Django Admin 配置。"""

from django.contrib import admin

from .models import Stock, StockLog


class StockLogInline(admin.TabularInline):
    model = StockLog
    extra = 0
    readonly_fields = ["change_quantity", "locked_change", "available_after", "reason", "created_at"]


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["sku", "quantity", "locked_quantity", "available", "version", "updated_at"]
    readonly_fields = ["available", "version"]
    inlines = [StockLogInline]


@admin.register(StockLog)
class StockLogAdmin(admin.ModelAdmin):
    list_display = ["stock", "change_quantity", "locked_change", "available_after", "reason", "created_at"]
    list_filter = ["reason"]
