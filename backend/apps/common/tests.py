"""通用模块测试：健康检查、模拟数据命令等。"""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.carts.models import CartItem
from apps.coupons.models import Coupon, UserCoupon
from apps.orders.models import Order
from apps.products.models import Brand, Category, SPU, SKU

User = get_user_model()


class HealthCheckTests(TestCase):
    """健康检查接口测试。"""

    def test_health_returns_ok(self):
        """健康检查应返回 200 与 ok 状态。"""
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["checks"]["database"], "ok")
        self.assertEqual(data["checks"]["redis"], "ok")


class SeedDemoDataTests(TestCase):
    """模拟数据命令测试。"""

    def test_seed_demo_data_creates_objects(self):
        """seed_demo_data 应创建管理员、用户、商品、优惠券、订单等数据。"""
        out = StringIO()
        call_command("seed_demo_data", stdout=out)

        self.assertIn("演示数据生成完成", out.getvalue())

        # 管理员 + 2 个普通用户
        self.assertTrue(User.objects.filter(username="admin", role=User.Role.ADMIN).exists())
        self.assertEqual(User.objects.filter(role=User.Role.CONSUMER).count(), 2)

        # 分类、品牌、SPU、SKU
        self.assertEqual(SPU.objects.count(), 3)
        self.assertEqual(SKU.objects.count(), 5)
        self.assertTrue(Category.objects.filter(name="手机通讯").exists())
        self.assertTrue(Brand.objects.filter(name="TechPro").exists())

        # 优惠券
        self.assertEqual(Coupon.objects.count(), 3)
        self.assertTrue(Coupon.objects.filter(code="NEW-USER-10").exists())
        self.assertEqual(UserCoupon.objects.count(), 6)  # 2 用户 × 3 券

        # 购物车
        self.assertEqual(CartItem.objects.count(), 3)

        # 订单
        self.assertEqual(Order.objects.count(), 2)

    def test_seed_demo_data_is_idempotent(self):
        """重复执行 seed_demo_data 不应重复创建数据。"""
        call_command("seed_demo_data")
        call_command("seed_demo_data")

        self.assertEqual(SPU.objects.count(), 3)
        self.assertEqual(SKU.objects.count(), 5)
        self.assertEqual(User.objects.filter(role=User.Role.CONSUMER).count(), 2)

    def test_seed_demo_data_clean(self):
        """--clean 参数应清空旧数据后重建。"""
        call_command("seed_demo_data")
        call_command("seed_demo_data", clean=True)

        self.assertEqual(SPU.objects.count(), 3)
        self.assertEqual(Order.objects.count(), 2)
