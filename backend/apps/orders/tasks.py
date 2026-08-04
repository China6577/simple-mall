"""订单模块 Celery 异步任务。"""

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from apps.common.mail import send_templated_email
from apps.inventory.services import release_stock

from .models import Order
from .services import cancel_order


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def auto_cancel_pending_order(self, order_id):
    """
    自动取消超时未支付订单并释放库存。

    由订单创建后延迟任务触发，仅当订单仍处于待支付状态时执行取消。
    """
    try:
        order = Order.objects.prefetch_related("items").get(id=order_id)
    except Order.DoesNotExist:
        return {"status": "skipped", "reason": "order_not_found"}

    if order.status != Order.Status.PENDING_PAYMENT:
        return {"status": "skipped", "reason": "status_not_pending"}

    # 二次校验：确保订单确实已超时，防止任务被提前执行或重复执行
    elapsed = (timezone.now() - order.created_at).total_seconds()
    if elapsed < settings.ORDER_AUTO_CANCEL_SECONDS:
        return {"status": "skipped", "reason": "not_yet_overdue"}

    # cancel_order 会校验权限并释放库存
    cancel_order(order, order.user)

    return {"status": "cancelled", "order_no": order.order_no}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def scan_and_cancel_overdue_orders(self):
    """
    兜底扫描：取消所有超时未支付的订单。

    由 Celery Beat 周期调度，用于处理延迟任务丢失或积压的场景。
    """
    deadline = timezone.now() - timezone.timedelta(seconds=settings.ORDER_AUTO_CANCEL_SECONDS)
    overdue_orders = Order.objects.filter(
        status=Order.Status.PENDING_PAYMENT,
        created_at__lte=deadline,
    )

    cancelled_count = 0
    for order in overdue_orders:
        auto_cancel_pending_order.delay(order.id)
        cancelled_count += 1

    return {"status": "scanned", "queued_count": cancelled_count}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_order_paid_email(self, order_id):
    """
    支付成功后异步发送邮件通知。

    开发/测试环境邮件输出到控制台或内存，不依赖 SMTP。
    """
    try:
        order = Order.objects.prefetch_related("items").get(id=order_id)
    except Order.DoesNotExist:
        return {"status": "skipped", "reason": "order_not_found"}

    if order.status != Order.Status.PAID:
        return {"status": "skipped", "reason": "order_not_paid"}

    item_lines = "\n".join(
        f"- {item.spu_name} x {item.quantity}  ¥{item.subtotal}"
        for item in order.items.all()
    )

    subject = f"订单支付成功 - {order.order_no}"
    message = (
        f"您好，{order.user.username}：\n\n"
        f"您的订单 {order.order_no} 已支付成功。\n"
        f"应付金额：¥{order.payable_amount}\n"
        f"支付时间：{order.paid_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        f"商品明细：\n{item_lines}\n\n"
        f"感谢您的购买！"
    )

    send_templated_email(
        subject=subject,
        message=message,
        recipient_list=[order.user.email] if order.user.email else [],
    )

    return {"status": "sent", "order_no": order.order_no}
