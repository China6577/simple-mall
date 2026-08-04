"""商品模块路由。"""

from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("brands/", views.BrandListView.as_view(), name="brand-list"),
    path("hot/", views.ProductHotView.as_view(), name="product-hot"),
    path("", views.SPUListView.as_view(), name="spu-list"),
    path("<int:pk>/", views.SPUDetailView.as_view(), name="spu-detail"),
]
