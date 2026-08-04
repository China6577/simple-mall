"""商品模块测试。"""

import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


class ProductAPITests(TestCase):
    """商品接口测试。"""

    def setUp(self):
        # 模型导入放在 setUp 中，避免 pytest 收集阶段因 Django 未 setup 而失败
        from apps.inventory.models import Stock
        from apps.products.models import Brand, Category, SKU, SPU

        self.Stock = Stock
        self.client = APIClient()
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
            stock=100,
            sales=10,
            status=True,
            is_default=True,
            specs={"颜色": "黑色", "容量": "128G"},
        )

    def _json(self, response):
        """获取渲染后的统一格式响应体。"""
        return json.loads(response.content)

    def test_create_sku_auto_creates_stock(self):
        """创建 SKU 时自动创建库存记录。"""
        stock = self.Stock.objects.filter(sku=self.sku).first()
        self.assertIsNotNone(stock)
        self.assertEqual(stock.quantity, 100)
        self.assertEqual(stock.locked_quantity, 0)

    def test_category_list(self):
        """分类列表接口返回 200。"""
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_brand_list(self):
        """品牌列表接口返回 200。"""
        response = self.client.get(reverse("brand-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_spu_list(self):
        """商品列表接口返回在售 SPU。"""
        response = self.client.get(reverse("spu-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["total"], 1)

    def test_spu_detail(self):
        """商品详情接口返回 SKU 和规格。"""
        response = self.client.get(reverse("spu-detail", kwargs={"pk": self.spu.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["code"], 0)
        self.assertEqual(body["data"]["name"], "iPhone 15")

    def test_spu_filter_by_category(self):
        """按分类筛选商品。"""
        response = self.client.get(reverse("spu-list"), {"category": self.category.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["data"]["total"], 1)

    def test_spu_search_keyword(self):
        """按关键词搜索商品。"""
        response = self.client.get(reverse("spu-list"), {"keyword": "iPhone"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        body = self._json(response)
        self.assertEqual(body["data"]["total"], 1)
