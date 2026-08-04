"""支付业务服务。"""

import uuid
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import BusinessException, ValidationException
from apps.inventory.services import deduct_stock
from apps.orders.models import Order
from apps.products.models import SKU

from django.db.models import F

from .models import PaymentRecord


def generate_payment_no():
    """生成唯一支付流水号。"""
    return f"P{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:8].upper()}"


def process_payment_callback(order_no, payment_no, amount, callback_data=None):
    """
    支付回调处理（幂等）。

    1. 使用 select_for_update 锁定订单，防止并发回调。
    2. 已支付订单直接返回原支付记录。
    3. 校验金额与状态。
    4. 扣减实际库存、更新订单状态、创建支付记录。
    """
    from apps.orders.models import Order

    if callback_data is None:
        callback_data = {}

    try:
        amount = Decimal(str(amount))
    except Exception as exc:
        raise ValidationException("支付金额格式错误") from exc

    with transaction.atomic():
        order = Order.objects.select_for_update().get(order_no=order_no)

        # 幂等：已支付直接返回原记录
        if order.status == Order.Status.PAID:
            return PaymentRecord.objects.filter(order=order).first()

        if order.status != Order.Status.PENDING_PAYMENT:
            raise BusinessException("订单状态不允许支付")

        if amount != order.payable_amount:
            raise BusinessException("支付金额不匹配")

        # 同一支付流水号不能重复处理
        if PaymentRecord.objects.filter(payment_no=payment_no).exists():
            raise BusinessException("支付流水已处理")

        # 扣减库存并累加 SKU 销量
        for item in order.items.all():
            deduct_stock(
                sku_id=item.sku_id,
                quantity=item.quantity,
                reason=f"订单 {order.order_no} 支付成功，扣减库存",
                operator=order.user,
            )
            SKU.objects.filter(id=item.sku_id).update(sales=F("sales") + item.quantity)

        # 更新订单
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at", "updated_at"])

        # 创建支付记录
        record = PaymentRecord.objects.create(
            order=order,
            payment_no=payment_no,
            amount=amount,
            status=PaymentRecord.Status.SUCCESS,
            paid_at=timezone.now(),
            callback_data=callback_data,
        )

    # 事务外触发：异步发送支付成功邮件
    from apps.orders.tasks import send_order_paid_email

    send_order_paid_email.delay(order.id)

    return record


def pay_order(order, user):
    """
    模拟支付入口。

    生成支付流水号后直接调用回调处理完成支付，用于教学和测试环境。
    """
    if order.user != user:
        raise BusinessException("无权操作该订单")
    if order.status != Order.Status.PENDING_PAYMENT:
        raise BusinessException("订单状态不允许支付")

    payment_no = generate_payment_no()
    process_payment_callback(
        order_no=order.order_no,
        payment_no=payment_no,
        amount=order.payable_amount,
        callback_data={"source": "simulated", "paid_by": user.username},
    )
    return payment_no
