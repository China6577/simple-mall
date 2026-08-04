"""订单模块测试。"""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class OrderAPITests(TestCase):
    """订单接口测试。"""

    def setUp(self):
        # 模型导入放在 setUp 中，避免 pytest 收集阶段因 Django 未 setup 而失败
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

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="StrongPass123",
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name="手机", level=1, sort_order=1)
        self.brand = Brand.objects.create(name="Apple", is_active=True)
        self.spu = SPU.objects.create(
            spu_code="SPU001",
            name="iPhone 15",
            category=self.category,
            brand=self.brand,
            description="最新款 iPhone",
            is_active=True,
        )
        self.sku = SKU.objects.create(
            sku_code="SKU001",
            spu=self.spu,
            price="5999.00",
            stock=10,
            sales=0,
            status=True,
            is_default=True,
            specs={"颜色": "黑色", "容量": "128G"},
        )

        self.address = Address.objects.create(
            user=self.user,
            receiver="张三",
            phone="13800138000",
            province="广东",
            city="深圳",
            district="南山",
            detail="科技园",
        )
        self.cart_item = CartItem.objects.create(user=self.user, sku=self.sku, quantity=2, selected=True)

    def _json(self, response):
        return json.loads(response.content)

    def _create_order(self):
        """辅助方法：创建订单并返回订单对象。"""
        response = self.client.post(
            reverse("order-list"),
            {"cart_item_ids": [self.cart_item.id], "address_id": self.address.id},
            format="json",
        )
        body = self._json(response)
        return response.status_code, body

    def test_create_order_success(self):
        """正常创建订单，锁定库存并删除购物车条目。"""
        status_code, body = self._create_order()
        self.assertEqual(status_code, status.HTTP_201_CREATED)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["status"], "pending_payment")
        self.assertEqual(Decimal(body["data"]["payable_amount"]), Decimal("11998.00"))

        # 购物车条目应被删除
        self.assertFalse(self.CartItem.objects.filter(id=self.cart_item.id).exists())

        # 库存应被锁定
        stock = self.Stock.objects.get(sku=self.sku)
        self.assertEqual(stock.locked_quantity, 2)
        self.assertEqual(stock.quantity, 10)
        self.assertEqual(stock.available, 8)

    def test_create_order_insufficient_stock(self):
        """库存不足时创建订单失败。"""
        self.cart_item.quantity = 100
        self.cart_item.save(update_fields=["quantity"])

        status_code, body = self._create_order()
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_inactive_sku(self):
        """SKU 下架时创建订单失败。"""
        self.sku.status = False
        self.sku.save(update_fields=["status"])

        status_code, body = self._create_order()
        self.assertEqual(status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_empty_cart(self):
        """空购物车创建订单失败。"""
        response = self.client.post(
            reverse("order-list"),
            {"cart_item_ids": [], "address_id": self.address.id},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_other_user_cart_item(self):
        """不能使用其他用户的购物车条目创建订单。"""
        other = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="StrongPass123",
        )
        other_cart = self.CartItem.objects.create(user=other, sku=self.sku, quantity=1, selected=True)

        response = self.client.post(
            reverse("order-list"),
            {"cart_item_ids": [other_cart.id], "address_id": self.address.id},
            format="json",
        )
        # 购物车条目不存在于当前用户，按空购物车处理
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_idempotency(self):
        """同一幂等键重复提交应被拒绝。"""
        key = "idem-key-001"
        self.client.post(
            reverse("order-list"),
            {
                "cart_item_ids": [self.cart_item.id],
                "address_id": self.address.id,
                "idempotency_key": key,
            },
            format="json",
        )

        # 重新创建购物车条目
        self.cart_item = self.CartItem.objects.create(user=self.user, sku=self.sku, quantity=2, selected=True)
        response = self.client.post(
            reverse("order-list"),
            {
                "cart_item_ids": [self.cart_item.id],
                "address_id": self.address.id,
                "idempotency_key": key,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cancel_order(self):
        """取消待支付订单，释放库存。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        response = self.client.post(reverse("order-cancel", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from apps.orders.models import Order

        order = Order.objects.get(order_no=order_no)
        self.assertEqual(order.status, Order.Status.CANCELLED)

        stock = self.Stock.objects.get(sku=self.sku)
        self.assertEqual(stock.locked_quantity, 0)
        self.assertEqual(stock.available, 10)

    def test_cancel_order_not_pending(self):
        """已支付订单不能取消。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))
        response = self.client.post(reverse("order-cancel", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pay_order(self):
        """支付订单，扣减实际库存。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        response = self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from apps.orders.models import Order

        order = Order.objects.get(order_no=order_no)
        self.assertEqual(order.status, Order.Status.PAID)

        stock = self.Stock.objects.get(sku=self.sku)
        self.assertEqual(stock.quantity, 8)
        self.assertEqual(stock.locked_quantity, 0)
        self.assertEqual(stock.available, 8)

    def test_pay_order_idempotency(self):
        """重复支付同一订单幂等。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))
        response = self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))
        # 第二次应返回成功或业务错误，但不修改状态
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_ship_order_by_operator(self):
        """运营人员可以发货。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]
        self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))

        operator = User.objects.create_user(
            username="operator1",
            email="operator1@example.com",
            password="StrongPass123",
            role="operator",
        )
        self.client.force_authenticate(user=operator)

        response = self.client.post(reverse("order-ship", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from apps.orders.models import Order

        order = Order.objects.get(order_no=order_no)
        self.assertEqual(order.status, Order.Status.SHIPPED)

    def test_ship_order_by_normal_user(self):
        """普通用户不能发货。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]
        self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))

        response = self.client.post(reverse("order-ship", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_receive_order(self):
        """用户确认收货。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]
        self.client.post(reverse("order-pay", kwargs={"order_no": order_no}))

        operator = User.objects.create_user(
            username="operator2",
            email="operator2@example.com",
            password="StrongPass123",
            role="operator",
        )
        self.client.force_authenticate(user=operator)
        self.client.post(reverse("order-ship", kwargs={"order_no": order_no}))

        self.client.force_authenticate(user=self.user)
        response = self.client.post(reverse("order-confirm", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        from apps.orders.models import Order

        order = Order.objects.get(order_no=order_no)
        self.assertEqual(order.status, Order.Status.COMPLETED)

    def test_order_list_and_detail(self):
        """订单列表与详情。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        response = self.client.get(reverse("order-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        list_body = self._json(response)
        self.assertEqual(list_body["code"], 0)
        self.assertEqual(list_body["data"]["total"], 1)

        response = self.client.get(reverse("order-detail", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        detail_body = self._json(response)
        self.assertEqual(detail_body["data"]["order_no"], order_no)
        self.assertEqual(len(detail_body["data"]["items"]), 1)

    def test_cannot_access_other_user_order(self):
        """不能查看其他用户的订单。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        other = User.objects.create_user(
            username="bob2",
            email="bob2@example.com",
            password="StrongPass123",
        )
        self.client.force_authenticate(user=other)
        response = self.client.get(reverse("order-detail", kwargs={"order_no": order_no}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_payment_callback(self):
        """支付回调接口幂等处理。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        from apps.payments.services import generate_payment_no

        payment_no = generate_payment_no()
        response = self.client.post(
            reverse("payment-callback"),
            {"order_no": order_no, "payment_no": payment_no, "amount": "11998.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 重复回调应幂等
        response = self.client.post(
            reverse("payment-callback"),
            {"order_no": order_no, "payment_no": payment_no, "amount": "11998.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_payment_callback_amount_mismatch(self):
        """回调金额不匹配应失败。"""
        _, body = self._create_order()
        order_no = body["data"]["order_no"]

        from apps.payments.services import generate_payment_no

        payment_no = generate_payment_no()
        response = self.client.post(
            reverse("payment-callback"),
            {"order_no": order_no, "payment_no": payment_no, "amount": "1.00"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
