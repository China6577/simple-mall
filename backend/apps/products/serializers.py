"""商品模块序列化器。"""

from django.db.models import Sum
from rest_framework import serializers

from .models import Brand, Category, ProductImage, SKU, SPU, SPUSpec, SpecOption


class CategorySerializer(serializers.ModelSerializer):
    """分类序列化器，包含子分类。"""

    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ["id", "name", "parent", "level", "sort_order", "is_active", "children"]

    def get_children(self, obj):
        """只递归一层子分类，避免嵌套过深。"""
        if obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []


class BrandSerializer(serializers.ModelSerializer):
    """品牌序列化器。"""

    class Meta:
        model = Brand
        fields = ["id", "name", "logo", "description", "is_active"]


class SpecOptionSerializer(serializers.ModelSerializer):
    """规格选项序列化器。"""

    class Meta:
        model = SpecOption
        fields = ["id", "value", "sort_order"]


class SPUSpecSerializer(serializers.ModelSerializer):
    """SPU 规格序列化器，包含选项列表。"""

    options = SpecOptionSerializer(many=True, read_only=True)

    class Meta:
        model = SPUSpec
        fields = ["id", "name", "sort_order", "options"]


class ProductImageSerializer(serializers.ModelSerializer):
    """商品图片序列化器。"""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "sort_order"]


class SKUSimpleSerializer(serializers.ModelSerializer):
    """SKU 简要序列化器，用于列表和详情中的规格展示。"""

    class Meta:
        model = SKU
        fields = ["id", "sku_code", "price", "stock", "sales", "status", "is_default", "specs"]


class SKUListSerializer(serializers.ModelSerializer):
    """SKU 列表序列化器，附带可售库存。"""

    available_stock = serializers.IntegerField(source="stock_record.available", read_only=True)

    class Meta:
        model = SKU
        fields = [
            "id", "sku_code", "price", "stock", "available_stock",
            "sales", "status", "is_default", "specs",
        ]


class SPUListSerializer(serializers.ModelSerializer):
    """SPU 列表序列化器：用于商品列表页。"""

    brand = BrandSerializer(read_only=True)
    default_sku = serializers.SerializerMethodField()
    main_image_url = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()

    class Meta:
        model = SPU
        fields = [
            "id", "spu_code", "name", "category", "brand",
            "description", "main_image", "main_image_url", "is_active", "default_sku",
            "sales",
        ]

    def get_default_sku(self, obj):
        """返回默认 SKU 或第一个在售 SKU 的价格和库存。"""
        sku = obj.skus.filter(status=True).order_by("-is_default", "id").first()
        if sku:
            return SKUSimpleSerializer(sku).data
        return None

    def get_main_image_url(self, obj):
        """返回主图完整 URL。"""
        request = self.context.get("request")
        if obj.main_image and request:
            return request.build_absolute_uri(obj.main_image.url)
        return obj.main_image.url if obj.main_image else ""

    def get_sales(self, obj):
        """返回该 SPU 下所有 SKU 的销量总和。"""
        return obj.skus.aggregate(total=Sum("sales"))["total"] or 0


class SPUDetailSerializer(serializers.ModelSerializer):
    """SPU 详情序列化器：用于商品详情页。"""

    brand = BrandSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    specs = SPUSpecSerializer(many=True, read_only=True)
    skus = SKUListSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    main_image_url = serializers.SerializerMethodField()
    sales = serializers.SerializerMethodField()

    class Meta:
        model = SPU
        fields = [
            "id", "spu_code", "name", "category", "brand",
            "description", "detail", "main_image", "main_image_url",
            "is_active", "specs", "skus", "images", "sales", "created_at",
        ]

    def get_main_image_url(self, obj):
        """返回主图完整 URL。"""
        request = self.context.get("request")
        if obj.main_image and request:
            return request.build_absolute_uri(obj.main_image.url)
        return obj.main_image.url if obj.main_image else ""

    def get_sales(self, obj):
        """返回该 SPU 下所有 SKU 的销量总和。"""
        return obj.skus.aggregate(total=Sum("sales"))["total"] or 0
