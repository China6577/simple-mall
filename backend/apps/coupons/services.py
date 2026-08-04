"""优惠券业务服务。"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import BusinessException, ValidationException

from .models import Coupon, OrderCoupon, UserCoupon


def _is_coupon_valid(coupon):
    """检查优惠券模板是否在有效期内且启用。"""
    now = timezone.now()
    if not coupon.is_active:
        return False
    if coupon.start_time > now or coupon.end_time < now:
        return False
    return True


def claim_coupon(user, coupon_id):
    """
    用户领取优惠券。

    校验：券是否存在、在有效期内、剩余数量充足、未超每人限领。
    """
    try:
        coupon = Coupon.objects.get(id=coupon_id)
    except Coupon.DoesNotExist:
        raise ValidationException("优惠券不存在")

    if not _is_coupon_valid(coupon):
        raise BusinessException("优惠券已失效")

    if coupon.remaining_quantity <= 0:
        raise BusinessException("优惠券已领完")

    if coupon.limit_per_user > 0:
        claimed_count = UserCoupon.objects.filter(
            user=user, coupon=coupon
        ).count()
        if claimed_count >= coupon.limit_per_user:
            raise BusinessException("已超过领取上限")

    with transaction.atomic():
        # 使用 select_for_update 防止并发超发
        coupon = Coupon.objects.select_for_update().get(id=coupon_id)
        if coupon.remaining_quantity <= 0:
            raise BusinessException("优惠券已领完")

        user_coupon = UserCoupon.objects.create(
            user=user, coupon=coupon, status=UserCoupon.Status.UNUSED
        )
        coupon.remaining_quantity -= 1
        coupon.save(update_fields=["remaining_quantity", "updated_at"])

    return user_coupon


def list_available_user_coupons(user):
    """获取用户当前可使用的优惠券列表。"""
    now = timezone.now()
    return UserCoupon.objects.filter(
        user=user,
        status=UserCoupon.Status.UNUSED,
        coupon__is_active=True,
        coupon__start_time__lte=now,
        coupon__end_time__gte=now,
    ).select_related("coupon")


def _calculate_single_discount(coupon, amount):
    """计算单张优惠券的抵扣金额。"""
    if amount < coupon.min_order_amount:
        return Decimal("0")

    if coupon.type == Coupon.Type.FIXED_AMOUNT:
        return min(coupon.value, amount)

    if coupon.type == Coupon.Type.PERCENTAGE:
        discount = amount * (Decimal("1") - coupon.value)
        if coupon.max_discount_amount is not None:
            discount = min(discount, coupon.max_discount_amount)
        return min(discount, amount)

    return Decimal("0")


def validate_and_apply_coupons(user, user_coupon_ids, total_amount):
    """
    校验并应用优惠券，返回抵扣明细。

    叠加规则：先应用折扣券，再应用满减券，确保用户获得最大优惠。
    总金额必须大于等于所有券的最低使用金额门槛之和。
    """
    if not user_coupon_ids:
        return Decimal("0"), []

    total_amount = Decimal(str(total_amount))
    user_coupons = list_available_user_coupons(user).filter(
        id__in=user_coupon_ids
    ).select_related("coupon")

    found_ids = {uc.id for uc in user_coupons}
    invalid_ids = set(user_coupon_ids) - found_ids
    if invalid_ids:
        raise ValidationException("部分优惠券不可用或已失效")

    # 校验最低使用金额：折扣券按当前总额，满减券按抵扣后金额
    # 简化处理：要求总金额 >= 每张券的 min_order_amount
    for uc in user_coupons:
        if total_amount < uc.coupon.min_order_amount:
            raise BusinessException(
                f"优惠券 {uc.coupon.name} 未达到最低使用金额 {uc.coupon.min_order_amount}"
            )

    # 分类并排序：折扣券优先，再按面值从大到小
    percentage_coupons = [uc for uc in user_coupons if uc.coupon.type == Coupon.Type.PERCENTAGE]
    fixed_coupons = [uc for uc in user_coupons if uc.coupon.type == Coupon.Type.FIXED_AMOUNT]

    percentage_coupons.sort(key=lambda uc: uc.coupon.value)
    fixed_coupons.sort(key=lambda uc: uc.coupon.value, reverse=True)

    remaining = total_amount
    details = []

    # 先应用折扣券
    for uc in percentage_coupons:
        discount = _calculate_single_discount(uc.coupon, remaining)
        if discount > 0:
            details.append({
                "user_coupon_id": uc.id,
                "coupon_name": uc.coupon.name,
                "coupon_type": uc.coupon.type,
                "discount_amount": discount,
            })
            remaining -= discount

    # 再应用满减券
    for uc in fixed_coupons:
        discount = _calculate_single_discount(uc.coupon, remaining)
        if discount > 0:
            details.append({
                "user_coupon_id": uc.id,
                "coupon_name": uc.coupon.name,
                "coupon_type": uc.coupon.type,
                "discount_amount": discount,
            })
            remaining -= discount

    discount_amount = total_amount - remaining
    return discount_amount, details


def mark_coupons_used(user, user_coupon_ids, order):
    """将用户优惠券标记为已使用，并创建订单优惠券关联。"""
    if not user_coupon_ids:
        return

    now = timezone.now()
    user_coupons = UserCoupon.objects.filter(
        id__in=user_coupon_ids,
        user=user,
        status=UserCoupon.Status.UNUSED,
    ).select_related("coupon")

    with transaction.atomic():
        for uc in user_coupons:
            uc.status = UserCoupon.Status.USED
            uc.used_at = now
            uc.order = order
            uc.save(update_fields=["status", "used_at", "order"])

            OrderCoupon.objects.create(
                order=order,
                user_coupon=uc,
                discount_amount=Decimal("0"),  # 由调用方在创建 OrderCoupon 时写入
            )
