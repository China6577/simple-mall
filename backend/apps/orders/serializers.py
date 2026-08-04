"""订单模块序列化器。"""

from rest_framework import serializers

from apps.coupons.models import OrderCoupon

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    """订单项序列化器。"""

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "sku_code",
            "spu_name",
            "specs",
            "main_image",
            "price",
            "quantity",
            "subtotal",
        ]


class OrderCreateSerializer(serializers.Serializer):
    """创建订单序列化器。"""

    cart_item_ids = serializers.ListField(
        child=serializers.IntegerField(),
        label="购物车条目 ID 列表",
        allow_empty=False,
    )
    address_id = serializers.IntegerField(label="收货地址 ID")
    remark = serializers.CharField(label="备注", required=False, allow_blank=True)
    idempotency_key = serializers.CharField(label="幂等键", required=False, allow_blank=True)
    coupon_ids = serializers.ListField(
        child=serializers.IntegerField(),
        label="用户优惠券 ID 列表",
        required=False,
        allow_empty=True,
    )


class OrderCouponSerializer(serializers.ModelSerializer):
    """订单使用优惠券序列化器。"""

    coupon_name = serializers.CharField(source="user_coupon.coupon.name", read_only=True)
    coupon_type = serializers.CharField(source="user_coupon.coupon.type", read_only=True)

    class Meta:
        model = OrderCoupon
        fields = [
            "id",
            "coupon_name",
            "coupon_type",
            "discount_amount",
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """订单列表序列化器。"""

    item_count = serializers.IntegerField(source="items.count", read_only=True)
    status_display = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "status",
            "status_display",
            "total_amount",
            "payable_amount",
            "item_count",
            "items",
            "created_at",
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()


class OrderDetailSerializer(serializers.ModelSerializer):
    """订单详情序列化器。"""

    items = OrderItemSerializer(many=True, read_only=True)
    coupons = OrderCouponSerializer(source="order_coupons", many=True, read_only=True)
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_no",
            "status",
            "status_display",
            "total_amount",
            "discount_amount",
            "freight_amount",
            "payable_amount",
            "address_snapshot",
            "remark",
            "items",
            "coupons",
            "paid_at",
            "shipped_at",
            "received_at",
            "cancelled_at",
            "created_at",
        ]

    def get_status_display(self, obj):
        return obj.get_status_display()
