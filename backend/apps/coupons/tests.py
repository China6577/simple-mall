"""优惠券模块测试。"""

import json
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.orders.models import Order

User = get_user_model()


class CouponAPITests(TestCase):
    """优惠券接口测试。"""

    def setUp(self):
        from apps.carts.models import CartItem
        from apps.coupons.models import Coupon
        from apps.inventory.models import Stock
        from apps.products.models import Brand, Category, SKU, SPU
        from apps.users.models import Address

        self.Coupon = Coupon
        self.CartItem = CartItem
        self.Stock = Stock
        self.Category = Category
        self.Brand = Brand
        self.SPU = SPU
        self.SKU = SKU
        self.Address = Address

        self.client = APIClient()
        self.user = User.objects.create_user(
            username="couponuser",
            email="coupon@example.com",
            password="StrongPass123",
        )
        self.client.force_authenticate(user=self.user)

        self.category = Category.objects.create(name="耳机", level=1, sort_order=1)
        self.brand = Brand.objects.create(name="Sony", is_active=True)
        self.spu = SPU.objects.create(
            spu_code="SPU-CP-001",
            name="降噪耳机",
            category=self.category,
            brand=self.brand,
            is_active=True,
        )
        self.sku = SKU.objects.create(
            sku_code="SKU-CP-001",
            spu=self.spu,
            price="1000.00",
            stock=10,
            sales=0,
            status=True,
            is_default=True,
            specs={"颜色": "黑色"},
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

        now = timezone.now()
        self.fixed_coupon = Coupon.objects.create(
            code="FIXED100",
            name="满500减100",
            type=Coupon.Type.FIXED_AMOUNT,
            value=Decimal("100.00"),
            min_order_amount=Decimal("500.00"),
            total_quantity=100,
            remaining_quantity=100,
            limit_per_user=2,
            start_time=now - timezone.timedelta(days=1),
            end_time=now + timezone.timedelta(days=7),
            is_active=True,
        )
        self.percent_coupon = Coupon.objects.create(
            code="PERCENT85",
            name="85折券",
            type=Coupon.Type.PERCENTAGE,
            value=Decimal("0.85"),
            min_order_amount=Decimal("0.00"),
            max_discount_amount=Decimal("200.00"),
            total_quantity=100,
            remaining_quantity=100,
            limit_per_user=2,
            start_time=now - timezone.timedelta(days=1),
            end_time=now + timezone.timedelta(days=7),
            is_active=True,
        )

    def _json(self, response):
        return json.loads(response.content)

    def test_list_claimable_coupons(self):
        """可领取优惠券列表。"""
        response = self.client.get(reverse("coupon-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["total"], 2)

    def test_claim_coupon(self):
        """领取优惠券。"""
        response = self.client.post(
            reverse("coupon-claim", kwargs={"coupon_id": self.fixed_coupon.id})
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.fixed_coupon.refresh_from_db()
        self.assertEqual(self.fixed_coupon.remaining_quantity, 99)

    def test_claim_coupon_exceeds_limit(self):
        """超过每人限领数量。"""
        url = reverse("coupon-claim", kwargs={"coupon_id": self.fixed_coupon.id})
        self.client.post(url)
        self.client.post(url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_calculate_coupon_discount(self):
        """优惠券试算：折扣券 + 满减券叠加。"""
        from apps.coupons.models import UserCoupon

        uc_fixed = UserCoupon.objects.create(
            user=self.user, coupon=self.fixed_coupon, status=UserCoupon.Status.UNUSED
        )
        uc_percent = UserCoupon.objects.create(
            user=self.user, coupon=self.percent_coupon, status=UserCoupon.Status.UNUSED
        )

        response = self.client.post(
            reverse("coupon-calculate"),
            {
                "coupon_ids": [uc_fixed.id, uc_percent.id],
                "total_amount": "1000.00",
            },
            format="json",
        )
        body = self._json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(body["code"], 0)
        # 先 85 折：1000 * 0.15 = 150（未超 200 上限），再满减 100
        self.assertEqual(Decimal(body["data"]["discount_amount"]), Decimal("250.00"))
        self.assertEqual(Decimal(body["data"]["payable_amount"]), Decimal("750.00"))

    def test_create_order_with_coupons(self):
        """下单时使用优惠券。"""
        from apps.coupons.models import UserCoupon

        cart_item = self.CartItem.objects.create(
            user=self.user, sku=self.sku, quantity=2, selected=True
        )
        uc = UserCoupon.objects.create(
            user=self.user, coupon=self.fixed_coupon, status=UserCoupon.Status.UNUSED
        )

        response = self.client.post(
            reverse("order-list"),
            {
                "cart_item_ids": [cart_item.id],
                "address_id": self.address.id,
                "coupon_ids": [uc.id],
            },
            format="json",
        )
        body = self._json(response)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(body["code"], 0)
        self.assertEqual(Decimal(body["data"]["total_amount"]), Decimal("2000.00"))
        self.assertEqual(Decimal(body["data"]["discount_amount"]), Decimal("100.00"))
        self.assertEqual(Decimal(body["data"]["payable_amount"]), Decimal("1900.00"))

        uc.refresh_from_db()
        self.assertEqual(uc.status, UserCoupon.Status.USED)

    def test_cancel_order_returns_coupons(self):
        """取消订单后优惠券应退回。"""
        from apps.coupons.models import UserCoupon

        cart_item = self.CartItem.objects.create(
            user=self.user, sku=self.sku, quantity=2, selected=True
        )
        uc = UserCoupon.objects.create(
            user=self.user, coupon=self.fixed_coupon, status=UserCoupon.Status.UNUSED
        )

        response = self.client.post(
            reverse("order-list"),
            {
                "cart_item_ids": [cart_item.id],
                "address_id": self.address.id,
                "coupon_ids": [uc.id],
            },
            format="json",
        )
        order_no = self._json(response)["data"]["order_no"]

        self.client.post(reverse("order-cancel", kwargs={"order_no": order_no}))

        uc.refresh_from_db()
        self.assertEqual(uc.status, UserCoupon.Status.UNUSED)
        self.assertIsNone(uc.used_at)

    def test_available_coupons_for_cart(self):
        """获取购物车可用优惠券。"""
        from apps.coupons.models import UserCoupon

        cart_item = self.CartItem.objects.create(
            user=self.user, sku=self.sku, quantity=2, selected=True
        )
        UserCoupon.objects.create(
            user=self.user, coupon=self.fixed_coupon, status=UserCoupon.Status.UNUSED
        )

        response = self.client.get(
            reverse("coupon-available"),
            {"cart_item_ids": str(cart_item.id)},
        )
        body = self._json(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(body["code"], 0)
        self.assertEqual(len(body["data"]["coupons"]), 1)
        self.assertEqual(
            Decimal(body["data"]["coupons"][0]["discount_amount"]),
            Decimal("100.00"),
        )
