"""优惠券模块路由。"""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CouponListView.as_view(), name="coupon-list"),
    path("my/", views.UserCouponListView.as_view(), name="user-coupon-list"),
    path("<int:coupon_id>/claim/", views.CouponClaimView.as_view(), name="coupon-claim"),
    path("calculate/", views.CouponCalculateView.as_view(), name="coupon-calculate"),
    path("available/", views.AvailableCouponForCartView.as_view(), name="coupon-available"),
]
