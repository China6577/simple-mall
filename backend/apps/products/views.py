"""商品模块视图。

提供分类、品牌、商品列表、商品详情等接口。
"""

from datetime import timedelta

from django.db.models import Max, Prefetch
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.pagination import StandardPagination

from .filters import SPUFilter
from .models import SKU, Brand, Category, SPU
from .serializers import (
    BrandSerializer,
    CategorySerializer,
    SPUListSerializer,
    SPUDetailSerializer,
)


class CategoryListView(generics.ListAPIView):
    """
    商品分类列表。

    只返回一级分类，每个分类下挂载二级子分类，
    避免一次性返回整棵树导致数据量过大。
    """

    queryset = Category.objects.filter(level=1, is_active=True).prefetch_related("children")
    serializer_class = CategorySerializer
    pagination_class = None  # 分类数量少，不分页


class BrandListView(generics.ListAPIView):
    """品牌列表。"""

    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    pagination_class = None


class SPUListView(generics.ListAPIView):
    """
    商品列表。

    支持：
    - 分页（page / page_size）
    - 搜索（?keyword=xxx）
    - 筛选（?category=1&brand=2&min_price=100&max_price=500）
    - 排序（?ordering=-created_at / name）
    - 热门商品（?hot=1，按 SKU 最大销量降序）
    - 新品推荐（?new=1，最近 30 天上架）
    """

    serializer_class = SPUListSerializer
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SPUFilter
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]
    ordering = ["-created_at"]

    def get_queryset(self):
        """根据查询参数动态构建 queryset。"""
        queryset = SPU.objects.filter(is_active=True).prefetch_related(
            Prefetch("skus", queryset=SKU.objects.filter(status=True)),
            "brand",
        )

        # 热门：按 SPU 下在售 SKU 的最大销量降序
        if self.request.query_params.get("hot"):
            queryset = queryset.annotate(max_sales=Max("skus__sales")).order_by("-max_sales", "-id")
            return queryset

        # 新品：最近 30 天上架
        if self.request.query_params.get("new"):
            recent = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=recent).order_by("-created_at")
            return queryset

        return queryset


class SPUDetailView(generics.RetrieveAPIView):
    """商品详情。"""

    queryset = SPU.objects.filter(is_active=True).prefetch_related(
        "specs__options", "skus__stock_record", "images"
    )
    serializer_class = SPUDetailSerializer
    # DRF RetrieveAPIView 默认 lookup_field="pk"，与 URL 中的 <int:pk> 保持一致
    lookup_field = "pk"


class ProductHotView(APIView):
    """热门商品接口（固定返回销量前 10）。"""

    def get(self, request):
        spus = (
            SPU.objects.filter(is_active=True)
            .annotate(max_sales=Max("skus__sales"))
            .order_by("-max_sales", "-id")
            .distinct()[:10]
        )
        serializer = SPUListSerializer(spus, many=True, context={"request": request})
        return Response(serializer.data)
