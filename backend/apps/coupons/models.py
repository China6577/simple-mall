"""优惠券模块模型。"""

from django.conf import settings
from django.db import models


class Coupon(models.Model):
    """优惠券模板：定义一张优惠券的规则与库存。"""

    class Type(models.TextChoices):
        FIXED_AMOUNT = "fixed_amount", "满减券"
        PERCENTAGE = "percentage", "折扣券"

    code = models.CharField("券码", max_length=64, unique=True, db_index=True)
    name = models.CharField("券名称", max_length=128)
    description = models.TextField("券说明", blank=True)
    type = models.CharField("类型", max_length=20, choices=Type.choices)
    # 满减券：固定减免金额；折扣券：折扣率（如 0.85 表示 85 折）
    value = models.DecimalField("面值/折扣率", max_digits=10, decimal_places=2)
    min_order_amount = models.DecimalField(
        "最低使用金额", max_digits=12, decimal_places=2, default=0
    )
    # 折扣券最大抵扣金额，避免高价值订单减免过多
    max_discount_amount = models.DecimalField(
        "最大抵扣金额", max_digits=12, decimal_places=2, null=True, blank=True
    )
    total_quantity = models.PositiveIntegerField("总发行量")
    remaining_quantity = models.PositiveIntegerField("剩余数量", default=0)
    # 每人限领数量，0 表示不限制
    limit_per_user = models.PositiveIntegerField("每人限领", default=1)
    start_time = models.DateTimeField("开始时间")
    end_time = models.DateTimeField("结束时间")
    is_active = models.BooleanField("是否启用", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "coupons_coupon"
        verbose_name = "优惠券"
        verbose_name_plural = "优惠券"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class UserCoupon(models.Model):
    """用户优惠券：记录用户领取的券及使用状态。"""

    class Status(models.TextChoices):
        UNUSED = "unused", "未使用"
        USED = "used", "已使用"
        EXPIRED = "expired", "已过期"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="coupons",
        verbose_name="用户",
    )
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.CASCADE,
        related_name="user_coupons",
        verbose_name="优惠券模板",
    )
    status = models.CharField(
        "状态", max_length=20, choices=Status.choices, default=Status.UNUSED
    )
    claimed_at = models.DateTimeField("领取时间", auto_now_add=True)
    used_at = models.DateTimeField("使用时间", null=True, blank=True)
    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="used_coupons",
        verbose_name="关联订单",
    )

    class Meta:
        db_table = "coupons_user_coupon"
        verbose_name = "用户优惠券"
        verbose_name_plural = "用户优惠券"
        ordering = ["-claimed_at"]

    def __str__(self):
        return f"{self.user.username} - {self.coupon.name}"


class OrderCoupon(models.Model):
    """订单使用的优惠券中间表，支持叠加。"""

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="order_coupons",
        verbose_name="订单",
    )
    user_coupon = models.ForeignKey(
        UserCoupon,
        on_delete=models.CASCADE,
        related_name="order_relations",
        verbose_name="用户优惠券",
    )
    discount_amount = models.DecimalField("抵扣金额", max_digits=12, decimal_places=2)

    class Meta:
        db_table = "coupons_order_coupon"
        verbose_name = "订单优惠券"
        verbose_name_plural = "订单优惠券"
        unique_together = [["order", "user_coupon"]]
