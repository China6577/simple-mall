"""订单业务服务。

封装订单创建、取消、支付、发货、确认收货等核心流程，
所有涉及库存的操作都委托给 inventory.services。
"""

import uuid
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from django.conf import settings

from apps.common.exceptions import BusinessException, ConflictException, ValidationException
from apps.inventory.services import deduct_stock, lock_stock, release_stock

from .models import Order, OrderItem


def generate_order_no():
    """生成唯一订单编号。"""
    return f"O{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


def _validate_cart_items(cart_items):
    """校验购物车条目是否可下单。"""
    if not cart_items:
        raise ValidationException("请选择购物车商品")

    for item in cart_items:
        if not item.sku.status or not item.sku.spu.is_active:
            raise BusinessException(f"商品 {item.sku.spu.name} 已下架")
        available = item.sku.stock_record.available if hasattr(item.sku, "stock_record") else item.sku.stock
        if item.quantity > available:
            raise BusinessException(f"商品 {item.sku.spu.name} 库存不足")


def create_order(user, cart_item_ids, address_id, remark="", idempotency_key="", coupon_ids=None):
    """
    创建订单。

    流程：
    1. 查询并校验购物车条目。
    2. 计算金额与优惠券抵扣，生成地址快照。
    3. 事务中：创建订单、锁定库存、创建订单项、关联优惠券、删除购物车条目。
    """
    from apps.carts.models import CartItem
    from apps.carts.services import delete_cart_summary_cache
    from apps.coupons.services import validate_and_apply_coupons
    from apps.users.models import Address

    coupon_ids = coupon_ids or []

    cart_items = CartItem.objects.filter(
        id__in=cart_item_ids, user=user, selected=True
    ).select_related("sku__spu", "sku__stock_record")

    _validate_cart_items(cart_items)

    try:
        address = Address.objects.get(id=address_id, user=user)
    except Address.DoesNotExist:
        raise ValidationException("收货地址不存在")

    address_snapshot = {
        "receiver": address.receiver,
        "phone": address.phone,
        "province": address.province,
        "city": address.city,
        "district": address.district,
        "detail": address.detail,
        "zip_code": address.zip_code,
    }

    total_amount = sum(item.sku.price * item.quantity for item in cart_items)
    freight_amount = Decimal("0")

    # 计算优惠券抵扣；此操作不修改数据库，仅做校验与计算
    discount_amount, coupon_details = validate_and_apply_coupons(
        user=user,
        user_coupon_ids=coupon_ids,
        total_amount=total_amount,
    )

    payable_amount = total_amount + freight_amount - discount_amount
    if payable_amount < 0:
        payable_amount = Decimal("0")

    # 按 SKU ID 排序后加锁，避免并发场景下死锁
    sorted_items = sorted(cart_items, key=lambda x: x.sku_id)

    with transaction.atomic():
        # 幂等：同一用户同一幂等键不能重复创建
        if idempotency_key:
            if Order.objects.filter(user=user, idempotency_key=idempotency_key).exists():
                raise ConflictException("订单已提交，请勿重复操作")

        order = Order.objects.create(
            order_no=generate_order_no(),
            user=user,
            status=Order.Status.PENDING_PAYMENT,
            total_amount=total_amount,
            discount_amount=discount_amount,
            freight_amount=freight_amount,
            payable_amount=payable_amount,
            address_snapshot=address_snapshot,
            remark=remark,
            idempotency_key=idempotency_key,
        )

        for item in sorted_items:
            lock_stock(
                sku_id=item.sku_id,
                quantity=item.quantity,
                reason=f"订单 {order.order_no} 创建，锁定库存",
                operator=user,
            )
            # 保存 SPU 主图相对路径作为订单快照
            main_image_path = ""
            if item.sku.spu.main_image:
                main_image_path = item.sku.spu.main_image.url
            OrderItem.objects.create(
                order=order,
                sku=item.sku,
                sku_code=item.sku.sku_code,
                spu_name=item.sku.spu.name,
                specs=item.sku.specs,
                main_image=main_image_path,
                price=item.sku.price,
                quantity=item.quantity,
                subtotal=item.sku.price * item.quantity,
            )

        # 关联优惠券并标记为已使用
        if coupon_details:
            from apps.coupons.models import OrderCoupon, UserCoupon

            now = timezone.now()
            for detail in coupon_details:
                uc = UserCoupon.objects.select_related("coupon").get(
                    id=detail["user_coupon_id"], user=user
                )
                uc.status = UserCoupon.Status.USED
                uc.used_at = now
                uc.order = order
                uc.save(update_fields=["status", "used_at", "order"])

                OrderCoupon.objects.create(
                    order=order,
                    user_coupon=uc,
                    discount_amount=detail["discount_amount"],
                )

        # 已下单的购物车条目删除
        cart_item_ids_list = [item.id for item in cart_items]
        CartItem.objects.filter(id__in=cart_item_ids_list).delete()

    # 删除购物车摘要缓存，避免下单后回到购物车仍显示旧数量
    delete_cart_summary_cache(user.id)

    # 事务外触发：订单创建成功后安排超时自动取消任务
    from .tasks import auto_cancel_pending_order

    auto_cancel_pending_order.apply_async(
        args=(order.id,),
        countdown=settings.ORDER_AUTO_CANCEL_SECONDS,
    )

    return order


def cancel_order(order, user):
    """取消订单：仅待支付订单可取消，释放锁定库存并退回优惠券。"""
    if order.user != user:
        raise BusinessException("无权操作该订单")
    if order.status != Order.Status.PENDING_PAYMENT:
        raise BusinessException("只能取消待支付订单")

    with transaction.atomic():
        for item in order.items.all():
            release_stock(
                sku_id=item.sku_id,
                quantity=item.quantity,
                reason=f"订单 {order.order_no} 取消，释放库存",
                operator=user,
            )

        # 退回已使用的优惠券
        from apps.coupons.models import UserCoupon

        for order_coupon in order.order_coupons.select_related("user_coupon"):
            uc = order_coupon.user_coupon
            uc.status = UserCoupon.Status.UNUSED
            uc.used_at = None
            uc.order = None
            uc.save(update_fields=["status", "used_at", "order"])

        order.status = Order.Status.CANCELLED
        order.cancelled_at = timezone.now()
        order.save(update_fields=["status", "cancelled_at", "updated_at"])

    return order


def ship_order(order, user):
    """发货：仅已支付订单可发货。"""
    if order.status != Order.Status.PAID:
        raise BusinessException("订单未支付，无法发货")

    order.status = Order.Status.SHIPPED
    order.shipped_at = timezone.now()
    order.save(update_fields=["status", "shipped_at", "updated_at"])
    return order


def confirm_receive_order(order, user):
    """确认收货：仅已发货订单可确认。"""
    if order.user != user:
        raise BusinessException("无权操作该订单")
    if order.status != Order.Status.SHIPPED:
        raise BusinessException("订单未发货，无法确认收货")

    order.status = Order.Status.COMPLETED
    order.received_at = timezone.now()
    order.save(update_fields=["status", "received_at", "updated_at"])
    return order
