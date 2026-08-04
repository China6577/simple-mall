"""订单模块路由。"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="order-list"),
    path("<str:order_no>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_no>/cancel/", views.OrderCancelView.as_view(), name="order-cancel"),
    path("<str:order_no>/pay/", views.OrderPayView.as_view(), name="order-pay"),
    path("<str:order_no>/ship/", views.OrderShipView.as_view(), name="order-ship"),
    path("<str:order_no>/confirm/", views.OrderConfirmView.as_view(), name="order-confirm"),
    path("<str:order_no>/delete/", views.OrderDeleteView.as_view(), name="order-delete"),
]
