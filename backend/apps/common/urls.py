"""通用接口路由。"""

from django.urls import path

from .views import health_check

urlpatterns = [
    path("", health_check, name="health"),
]
