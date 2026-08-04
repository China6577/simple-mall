"""Django Admin 用户与地址管理。"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Address, User


class AddressInline(admin.TabularInline):
    """用户详情页 inline 展示收货地址。"""

    model = Address
    extra = 1
    fields = ["receiver", "phone", "province", "city", "district", "detail", "is_default"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "phone", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active", "is_staff", "date_joined"]
    search_fields = ["username", "email", "phone"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("扩展信息", {"fields": ("phone", "avatar", "role")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ("扩展信息", {"fields": ("phone", "role")}),
    )
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ["user", "receiver", "phone", "province", "city", "district", "is_default", "created_at"]
    list_filter = ["province", "is_default", "created_at"]
    search_fields = ["user__username", "receiver", "phone", "detail"]
    readonly_fields = ["created_at", "updated_at"]
