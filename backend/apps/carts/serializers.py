"""购物车模块序列化器。"""

from decimal import Decimal

from rest_framework import serializers

from apps.products.serializers import SKUListSerializer

from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """购物车列表/详情序列化器，附带 SKU 和 SPU 摘要。"""

    sku = SKUListSerializer(read_only=True)
    spu_name = serializers.CharField(source="sku.spu.name", read_only=True)
    spu_main_image = serializers.SerializerMethodField()
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            "id",
            "sku",
            "spu_name",
            "spu_main_image",
            "quantity",
            "selected",
            "subtotal",
            "created_at",
        ]

    def get_spu_main_image(self, obj):
        """返回 SPU 主图完整 URL。"""
        request = self.context.get("request")
        image = obj.sku.spu.main_image
        if image and request:
            return request.build_absolute_uri(image.url)
        return image.url if image else ""

    def get_subtotal(self, obj):
        """单种 SKU 小计 = 售价 × 数量。"""
        return obj.sku.price * obj.quantity


class CartItemCreateSerializer(serializers.ModelSerializer):
    """添加商品到购物车：传入 sku_id 和 quantity。"""

    sku_id = serializers.IntegerField(label="SKU ID", write_only=True)

    class Meta:
        model = CartItem
        fields = ["sku_id", "quantity"]

    def validate_sku_id(self, value):
        """校验 SKU 存在、上架，并缓存到 self.sku 供后续使用。"""
        from apps.products.models import SKU

        try:
            self.sku = (
                SKU.objects.select_related("spu", "stock_record")
                .get(id=value, status=True, spu__is_active=True)
            )
        except SKU.DoesNotExist:
            raise serializers.ValidationError("商品不存在或已下架")
        return value

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("数量至少为 1")
        return value

    def validate(self, attrs):
        sku = getattr(self, "sku", None)
        if sku is None:
            # 防御：如果 validate_sku_id 因某种原因未执行，重新查询
            from apps.products.models import SKU
            sku = SKU.objects.select_related("stock_record").get(id=attrs["sku_id"])

        available = sku.stock_record.available if hasattr(sku, "stock_record") else sku.stock
        if attrs["quantity"] > available:
            raise serializers.ValidationError("库存不足")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user
        sku = self.sku
        quantity = validated_data["quantity"]

        item, created = CartItem.objects.get_or_create(
            user=user,
            sku=sku,
            defaults={"quantity": quantity, "selected": True},
        )
        if not created:
            # 已存在则累加数量，但不超过当前可售库存
            available = sku.stock_record.available if hasattr(sku, "stock_record") else sku.stock
            item.quantity = min(item.quantity + quantity, available)
            item.selected = True
            item.save(update_fields=["quantity", "selected", "updated_at"])
        return item


class CartItemUpdateSerializer(serializers.ModelSerializer):
    """修改购物车条目：数量和选中状态。"""

    class Meta:
        model = CartItem
        fields = ["quantity", "selected"]

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("数量至少为 1")

        item = self.instance
        available = item.sku.stock_record.available
        if value > available:
            raise serializers.ValidationError("库存不足")
        return value
