"""商品 Celery 异步任务测试。"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from apps.orders.models import Order
from apps.products.models import SKU
from apps.products.tasks import check_low_stock_and_alert, refresh_product_sales_stats

User = get_user_model()


class ProductTaskTests(TestCase):
    """商品异步任务测试。"""

    def setUp(self):
        from apps.inventory.models import Stock
        from apps.products.models import Brand, Category, SPU
        from apps.users.models import Address

        self.Stock = Stock
        self.Category = Category
        self.Brand = Brand
        self.SPU = SPU
        self.SKU = SKU
        self.Address = Address

        self.user = User.objects.create_user(
            username="producttask",
            email="producttask@example.com",
            password="StrongPass123",
        )

        self.category = Category.objects.create(name="平板", level=1, sort_order=1)
        self.brand = Brand.objects.create(name="Xiaomi", is_active=True)
        self.spu = SPU.objects.create(
            spu_code="SPU-PT-001",
            name="小米平板 6",
            category=self.category,
            brand=self.brand,
            is_active=True,
        )
        self.sku_price = Decimal("1999.00")
        self.sku = SKU.objects.create(
            sku_code="SKU-PT-001",
            spu=self.spu,
            price=self.sku_price,
            stock=10,
            sales=0,
            status=True,
            is_default=True,
            specs={"颜色": "银色"},
        )

    def test_check_low_stock_alert(self):
        """低库存检查应返回预警商品列表。"""
        stock = self.Stock.objects.get(sku=self.sku)
        stock.quantity = 8
        stock.locked_quantity = 5
        stock.save(update_fields=["quantity", "locked_quantity"])

        # 清除缓存，确保任务可以执行
        cache.delete("tasks:low_stock_alert:last_run")

        result = check_low_stock_and_alert.run(threshold=5)

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["alert_count"], 1)
        self.assertEqual(result["items"][0]["sku_code"], self.sku.sku_code)

    def test_refresh_product_sales_stats(self):
        """销量统计刷新应更新 SKU.sales 并写入缓存。"""
        # 构造已支付订单
        order = Order.objects.create(
            order_no="O-PT-001",
            user=self.user,
            status=Order.Status.PAID,
            total_amount=self.sku_price,
            payable_amount=self.sku_price,
            address_snapshot={},
        )
        order.items.create(
            sku=self.sku,
            sku_code=self.sku.sku_code,
            spu_name=self.spu.name,
            specs=self.sku.specs,
            price=self.sku_price,
            quantity=3,
            subtotal=self.sku_price * 3,
        )

        result = refresh_product_sales_stats.run()

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["sku_count"], 1)
        self.assertEqual(result["spu_count"], 1)
        self.assertEqual(result["category_count"], 1)

        self.sku.refresh_from_db()
        self.assertEqual(self.sku.sales, 3)

        spu_sales = cache.get("stats:spu_sales")
        self.assertIsNotNone(spu_sales)
        self.assertEqual(spu_sales[self.spu.id], 3)
