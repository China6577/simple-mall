"""优惠券模块视图。"""

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import BusinessException, NotFoundException, ValidationException
from apps.common.pagination import StandardPagination

from .models import Coupon, UserCoupon
from .serializers import (
    CouponCalculateSerializer,
    CouponSerializer,
    UserCouponSerializer,
)
from .services import (
    _calculate_single_discount,
    claim_coupon,
    list_available_user_coupons,
    validate_and_apply_coupons,
)


class CouponListView(generics.ListAPIView):
    """可领取优惠券列表。"""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    serializer_class = CouponSerializer

    def get_queryset(self):
        now = timezone.now()
        return Coupon.objects.filter(
            is_active=True,
            start_time__lte=now,
            end_time__gte=now,
            remaining_quantity__gt=0,
        )


class UserCouponListView(generics.ListAPIView):
    """我的优惠券列表。"""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination
    serializer_class = UserCouponSerializer

    def get_queryset(self):
        status_filter = self.request.query_params.get("status")
        queryset = UserCoupon.objects.filter(user=self.request.user).select_related("coupon")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by("-claimed_at")


class CouponClaimView(APIView):
    """领取优惠券。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, coupon_id):
        try:
            user_coupon = claim_coupon(request.user, coupon_id)
        except Coupon.DoesNotExist:
            raise NotFoundException("优惠券不存在")
        except BusinessException as exc:
            raise BusinessException(str(exc))

        return Response(
            {"message": "领取成功", "id": user_coupon.id},
            status=status.HTTP_201_CREATED,
        )


class CouponCalculateView(APIView):
    """优惠券试算：根据商品总额计算可抵扣金额。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CouponCalculateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        coupon_ids = serializer.validated_data["coupon_ids"]
        total_amount = serializer.validated_data["total_amount"]

        discount_amount, details = validate_and_apply_coupons(
            user=request.user,
            user_coupon_ids=coupon_ids,
            total_amount=total_amount,
        )

        return Response({
            "total_amount": total_amount,
            "discount_amount": discount_amount,
            "payable_amount": total_amount - discount_amount,
            "coupons": details,
        })


class AvailableCouponForCartView(APIView):
    """获取当前购物车选中商品的优惠券列表（含不可用券）。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from apps.carts.models import CartItem
        from decimal import Decimal

        cart_item_ids = request.query_params.get("cart_item_ids", "")
        if not cart_item_ids:
            raise ValidationException("请传入购物车条目 ID")

        try:
            ids = [int(i) for i in cart_item_ids.split(",") if i.strip()]
        except ValueError:
            raise ValidationException("购物车条目 ID 格式错误")

        cart_items = CartItem.objects.filter(
            id__in=ids, user=request.user, selected=True
        ).select_related("sku")

        total_amount = sum(item.sku.price * item.quantity for item in cart_items)

        user_coupons = list_available_user_coupons(request.user)
        coupons = []
        for uc in user_coupons:
            coupon = uc.coupon
            usable = total_amount >= coupon.min_order_amount
            discount = Decimal("0")
            if usable:
                discount = _calculate_single_discount(coupon, total_amount)
            coupons.append({
                "user_coupon": UserCouponSerializer(uc).data,
                "discount_amount": discount,
                "usable": usable,
                "reason": "" if usable else f"满¥{coupon.min_order_amount}可用",
            })

        # 可用券排在前面
        coupons.sort(key=lambda x: (not x["usable"], -x["discount_amount"]))

        return Response({
            "total_amount": total_amount,
            "coupons": coupons,
        })
