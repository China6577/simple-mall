"""支付模块路由。"""

from django.urls import path

from . import views

urlpatterns = [
    path("callback/", views.PaymentCallbackView.as_view(), name="payment-callback"),
]
