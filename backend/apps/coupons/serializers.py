"""优惠券模块序列化器。"""

from rest_framework import serializers

from .models import Coupon, UserCoupon


class CouponSerializer(serializers.ModelSerializer):
    """优惠券模板序列化器。"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)
    is_claimable = serializers.SerializerMethodField()

    class Meta:
        model = Coupon
        fields = [
            "id",
            "code",
            "name",
            "description",
            "type",
            "type_display",
            "value",
            "min_order_amount",
            "max_discount_amount",
            "total_quantity",
            "remaining_quantity",
            "limit_per_user",
            "start_time",
            "end_time",
            "is_active",
            "is_claimable",
            "created_at",
        ]

    def get_is_claimable(self, obj):
        from django.utils import timezone

        now = timezone.now()
        return (
            obj.is_active
            and obj.start_time <= now <= obj.end_time
            and obj.remaining_quantity > 0
        )


class UserCouponSerializer(serializers.ModelSerializer):
    """用户优惠券序列化器。"""

    coupon = CouponSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = UserCoupon
        fields = [
            "id",
            "coupon",
            "status",
            "status_display",
            "claimed_at",
            "used_at",
        ]


class CouponCalculateSerializer(serializers.Serializer):
    """优惠券试算序列化器。"""

    coupon_ids = serializers.ListField(
        child=serializers.IntegerField(),
        label="用户优惠券 ID 列表",
        allow_empty=False,
    )
    total_amount = serializers.DecimalField(
        label="商品总金额", max_digits=12, decimal_places=2
    )
