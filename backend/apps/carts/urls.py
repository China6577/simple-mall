"""购物车模块路由。"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CartListView.as_view(), name="cart-list"),
    path("items/", views.CartItemCreateView.as_view(), name="cart-item-create"),
    path("items/<int:pk>/", views.CartItemDetailView.as_view(), name="cart-item-detail"),
    path("select/", views.CartSelectView.as_view(), name="cart-select"),
]
