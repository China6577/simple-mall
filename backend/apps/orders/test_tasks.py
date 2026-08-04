"""订单 Celery 异步任务测试。"""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from apps.orders.models import Order
from apps.orders.tasks import (
    auto_cancel_pending_order,
    scan_and_cancel_overdue_orders,
    send_order_paid_email,
)

User = get_user_model()


class OrderTaskTests(TestCase):
    """订单异步任务测试。"""

    def setUp(self):
        from apps.carts.models import CartItem
        from apps.inventory.models import Stock
        from apps.products.models import Brand, Category, SKU, SPU
        from apps.users.models import Address

        self.CartItem = CartItem
        self.Stock = Stock
        self.Category = Category
        self.Brand = Brand
        self.SPU = SPU
        self.SKU = SKU
        self.Address = Address

        self.user = User.objects.create_user(
            username="taskuser",
            email="taskuser@example.com",
            password="StrongPass123",
        )

        self.category = Category.objects.create(name="耳机", level=1, sort_order=1)
        self.brand = Brand.objects.create(name="Sony", is_active=True)
        self.spu = SPU.objects.create(
            spu_code="SPU-TASK-001",
            name="WH-1000XM5",
            category=self.category,
            brand=self.brand,
            is_active=True,
        )
        self.sku = SKU.objects.create(
            sku_code="SKU-TASK-001",
            spu=self.spu,
            price="1999.00",
            stock=10,
            sales=0,
            status=True,
            is_default=True,
            specs={"颜色": "黑色"},
        )

        self.address = Address.objects.create(
            user=self.user,
            receiver="李四",
            phone="13800138001",
            province="上海",
            city="上海",
            district="浦东",
            detail="陆家嘴",
        )

    def _create_pending_order(self):
        """辅助方法：直接创建一个待支付订单。"""
        from apps.inventory.services import lock_stock

        order = Order.objects.create(
            order_no="O-TASK-001",
            user=self.user,
            status=Order.Status.PENDING_PAYMENT,
            total_amount=self.sku.price,
            payable_amount=self.sku.price,
            address_snapshot={"receiver": "李四"},
        )
        order.items.create(
            sku=self.sku,
            sku_code=self.sku.sku_code,
            spu_name=self.spu.name,
            specs=self.sku.specs,
            price=self.sku.price,
            quantity=1,
            subtotal=self.sku.price,
        )
        lock_stock(
            sku_id=self.sku.id,
            quantity=1,
            reason=f"订单 {order.order_no} 创建，锁定库存",
            operator=self.user,
        )
        return order

    def test_auto_cancel_skips_if_not_overdue(self):
        """未超时的待支付订单不应被取消。"""
        order = self._create_pending_order()

        result = auto_cancel_pending_order.run(order.id)

        self.assertEqual(result["status"], "skipped")
        self.assertEqual(result["reason"], "not_yet_overdue")

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PENDING_PAYMENT)

    def test_auto_cancel_overdue_order(self):
        """超时的待支付订单应被取消并释放库存。"""
        order = self._create_pending_order()
        # 将订单创建时间改为超时前
        order.created_at = timezone.now() - timedelta(
            seconds=settings.ORDER_AUTO_CANCEL_SECONDS + 1
        )
        order.save(update_fields=["created_at"])

        result = auto_cancel_pending_order.run(order.id)

        self.assertEqual(result["status"], "cancelled")
        self.assertEqual(result["order_no"], order.order_no)

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)

        stock = self.Stock.objects.get(sku=self.sku)
        self.assertEqual(stock.locked_quantity, 0)
        self.assertEqual(stock.available, 10)

    def test_send_order_paid_email(self):
        """支付成功后应发送邮件通知。"""
        order = self._create_pending_order()
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=["status", "paid_at"])

        result = send_order_paid_email.run(order.id)

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["order_no"], order.order_no)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(order.order_no, mail.outbox[0].subject)
        self.assertIn(str(order.user.email), mail.outbox[0].to)

    def test_scan_and_cancel_overdue_orders(self):
        """扫描任务应将超时订单加入取消队列。"""
        order = self._create_pending_order()
        order.created_at = timezone.now() - timedelta(
            seconds=settings.ORDER_AUTO_CANCEL_SECONDS + 1
        )
        order.save(update_fields=["created_at"])

        result = scan_and_cancel_overdue_orders.run()

        self.assertEqual(result["status"], "scanned")
        self.assertEqual(result["queued_count"], 1)

        # 在 eager 模式下，auto_cancel_pending_order 会立即执行
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
