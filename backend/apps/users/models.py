"""用户模型与地址模型。"""

from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.common.models import BaseModel


class User(AbstractUser):
    """
    自定义用户模型。

    继承 AbstractUser，保留 Django 内置的密码哈希、权限组、is_active 等字段，
    并扩展电商业务需要的字段。

    设计约定：
    - 邮箱（email）唯一，作为登录标识（USERNAME_FIELD）。
    - 用户名（username）仅用于展示，允许重复。
    """

    class Role(models.TextChoices):
        CONSUMER = "consumer", "普通用户"
        OPERATOR = "operator", "运营人员"
        ADMIN = "admin", "管理员"

    # 覆盖 AbstractUser 字段：用户名允许重复，邮箱必须唯一且非空
    username = models.CharField("用户名", max_length=150, blank=False)
    email = models.EmailField("邮箱", unique=True, blank=False)

    phone = models.CharField("手机号", max_length=20, blank=True, default="")
    avatar = models.ImageField("头像", upload_to="avatars/", blank=True, default="")
    role = models.CharField("角色", max_length=20, choices=Role.choices, default=Role.CONSUMER)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "users_user"
        verbose_name = "用户"
        verbose_name_plural = "用户"
        ordering = ["-date_joined"]


class Address(BaseModel):
    """
    用户收货地址。

    每个用户可以保存多个地址，其中一个是默认地址。
    """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses", verbose_name="用户")
    receiver = models.CharField("收货人", max_length=50)
    phone = models.CharField("手机号", max_length=20)
    province = models.CharField("省份", max_length=50)
    city = models.CharField("城市", max_length=50)
    district = models.CharField("区县", max_length=50, blank=True, default="")
    detail = models.CharField("详细地址", max_length=200)
    zip_code = models.CharField("邮编", max_length=10, blank=True, default="")
    is_default = models.BooleanField("是否默认", default=False)

    class Meta:
        db_table = "users_address"
        verbose_name = "收货地址"
        verbose_name_plural = "收货地址"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.receiver} - {self.province}{self.city}{self.district}{self.detail}"
