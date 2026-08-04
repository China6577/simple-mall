"""商品模块筛选器。"""

import django_filters

from .models import SPU


class SPUFilter(django_filters.FilterSet):
    """商品列表筛选：分类、品牌、价格区间、搜索关键词、排序。"""

    # 按分类 ID 精确匹配
    category = django_filters.NumberFilter(field_name="category_id")
    # 按品牌 ID 精确匹配
    brand = django_filters.NumberFilter(field_name="brand_id")
    # 价格区间基于默认 SKU 的价格，这里简化为按 SPU 下 SKU 的最小价格过滤
    min_price = django_filters.NumberFilter(
        field_name="skus__price", lookup_expr="gte", distinct=True
    )
    max_price = django_filters.NumberFilter(
        field_name="skus__price", lookup_expr="lte", distinct=True
    )
    # 关键词搜索：商品名称
    keyword = django_filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = SPU
        fields = ["category", "brand", "keyword"]
