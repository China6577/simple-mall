"""商品模块 Django Admin 配置。"""

from django.contrib import admin

from .models import Brand, Category, ProductImage, SKU, SPU, SPUSpec, SpecOption


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "level", "sort_order", "is_active"]
    list_filter = ["level", "is_active"]
    search_fields = ["name"]


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name"]


class SKUInline(admin.TabularInline):
    model = SKU
    extra = 1
    fields = ["sku_code", "price", "stock", "sales", "status", "is_default"]


class SPUSpecInline(admin.TabularInline):
    model = SPUSpec
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(SPU)
class SPUAdmin(admin.ModelAdmin):
    list_display = ["spu_code", "name", "category", "brand", "is_active", "created_at"]
    list_filter = ["category", "brand", "is_active"]
    search_fields = ["spu_code", "name"]
    inlines = [SPUSpecInline, SKUInline, ProductImageInline]


@admin.register(SKU)
class SKUAdmin(admin.ModelAdmin):
    list_display = ["sku_code", "spu", "price", "stock", "sales", "status"]
    list_filter = ["status", "spu__category"]
    search_fields = ["sku_code", "spu__name"]


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ["id", "spu", "sku", "sort_order"]
