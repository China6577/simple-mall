"""购物车模块测试。"""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class CartAPITests(TestCase):
    """购物车接口测试。"""

    def setUp(self):
        # 模型导入放在 setUp 中，避免 pytest 收集阶段因 Django 未 setup 而失败
        from apps.products.models import Brand, Category, SKU, SPU

        self.Category = Category
        self.Brand = Brand
        self.SPU = SPU
        self.SKU = SKU

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
        self.sku2 = SKU.objects.create(
            sku_code="SKU002",
            spu=self.spu,
            price="6999.00",
            stock=5,
            sales=0,
            status=True,
            is_default=False,
            specs={"颜色": "白色", "容量": "256G"},
        )

    def _json(self, response):
        return json.loads(response.content)

    def _create_cart_item(self, sku, quantity=1):
        """辅助方法：直接创建购物车条目。"""
        from apps.carts.models import CartItem

        return CartItem.objects.create(user=self.user, sku=sku, quantity=quantity)

    def test_add_to_cart(self):
        """正常添加商品到购物车。"""
        response = self.client.post(
            reverse("cart-item-create"),
            {"sku_id": self.sku.id, "quantity": 2},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["quantity"], 2)

    def test_add_same_sku_accumulates_quantity(self):
        """重复添加同一 SKU，数量应累加。"""
        self.client.post(
            reverse("cart-item-create"),
            {"sku_id": self.sku.id, "quantity": 2},
            format="json",
        )
        response = self.client.post(
            reverse("cart-item-create"),
            {"sku_id": self.sku.id, "quantity": 3},
            format="json",
        )
        body = self._json(response)
        self.assertEqual(body["data"]["quantity"], 5)

    def test_add_to_cart_exceeds_stock(self):
        """添加数量超过库存应返回 400。"""
        response = self.client.post(
            reverse("cart-item-create"),
            {"sku_id": self.sku.id, "quantity": 100},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_add_inactive_sku_fails(self):
        """不能添加已下架 SKU。"""
        self.sku.status = False
        self.sku.save(update_fields=["status"])
        response = self.client.post(
            reverse("cart-item-create"),
            {"sku_id": self.sku.id, "quantity": 1},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_cart(self):
        """查询购物车返回条目和摘要。"""
        self._create_cart_item(self.sku, 2)
        self._create_cart_item(self.sku2, 1)

        response = self.client.get(reverse("cart-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(len(body["data"]["items"]), 2)
        # 两个都选中，总金额 = 5999*2 + 6999*1 = 18997
        self.assertEqual(body["data"]["summary"]["total_count"], 3)
        self.assertEqual(body["data"]["summary"]["selected_count"], 3)
        self.assertEqual(Decimal(body["data"]["summary"]["total_amount"]), Decimal("18997.00"))

    def test_update_cart_item_quantity(self):
        """修改购物车条目数量。"""
        item = self._create_cart_item(self.sku, 1)
        response = self.client.put(
            reverse("cart-item-detail", kwargs={"pk": item.id}),
            {"quantity": 5},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["data"]["quantity"], 5)

    def test_update_cart_item_selected(self):
        """取消选中后摘要变化。"""
        item = self._create_cart_item(self.sku, 2)
        response = self.client.put(
            reverse("cart-item-detail", kwargs={"pk": item.id}),
            {"selected": False},
            format="json",
        )
        body = self._json(response)
        self.assertEqual(body["data"]["selected"], False)

    def test_delete_cart_item(self):
        """删除购物车条目。"""
        item = self._create_cart_item(self.sku, 1)
        response = self.client.delete(reverse("cart-item-detail", kwargs={"pk": item.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["message"], "删除成功")
        self.assertFalse(item.__class__.objects.filter(id=item.id).exists())

    def test_batch_select(self):
        """批量选中/取消。"""
        item1 = self._create_cart_item(self.sku, 1)
        item2 = self._create_cart_item(self.sku2, 1)
        # 先把两个都设为非选中
        item1.selected = False
        item2.selected = False
        item1.save(update_fields=["selected"])
        item2.save(update_fields=["selected"])

        response = self.client.post(
            reverse("cart-select"),
            {"item_ids": [item1.id, item2.id], "selected": True},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)

    def test_cannot_access_other_users_cart(self):
        """不能操作其他用户的购物车条目。"""
        other = User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="StrongPass123",
        )
        from apps.carts.models import CartItem

        item = CartItem.objects.create(user=other, sku=self.sku, quantity=1)
        response = self.client.delete(reverse("cart-item-detail", kwargs={"pk": item.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_access_cart(self):
        """未登录用户无法访问购物车。"""
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("cart-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
