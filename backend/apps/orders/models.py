"""订单模块模型。"""

from django.conf import settings
from django.db import models


class Order(models.Model):
    """订单主表。"""

    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "待支付"
        PAID = "paid", "已支付"
        SHIPPED = "shipped", "已发货"
        COMPLETED = "completed", "已完成"
        CANCELLED = "cancelled", "已取消"
        REFUNDING = "refunding", "退款中"
        REFUNDED = "refunded", "已退款"

    order_no = models.CharField("订单编号", max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="用户",
    )
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_PAYMENT,
    )
    total_amount = models.DecimalField("商品总金额", max_digits=12, decimal_places=2)
    discount_amount = models.DecimalField("优惠金额", max_digits=12, decimal_places=2, default=0)
    freight_amount = models.DecimalField("运费", max_digits=12, decimal_places=2, default=0)
    payable_amount = models.DecimalField("应付金额", max_digits=12, decimal_places=2)
    # 优惠券字段在阶段八实现，此处预留注释
    # coupon = models.ForeignKey("coupons.UserCoupon", on_delete=models.SET_NULL, null=True, blank=True)
    address_snapshot = models.JSONField("收货地址快照", default=dict)
    remark = models.CharField("备注", max_length=255, blank=True)
    idempotency_key = models.CharField("幂等键", max_length=128, blank=True, db_index=True)
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    shipped_at = models.DateTimeField("发货时间", null=True, blank=True)
    received_at = models.DateTimeField("收货时间", null=True, blank=True)
    cancelled_at = models.DateTimeField("取消时间", null=True, blank=True)
    is_deleted = models.BooleanField("已删除", default=False)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "orders_order"
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ["-created_at"]

    def __str__(self):
        return self.order_no


class OrderItem(models.Model):
    """订单项：保存下单瞬间的商品快照。"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="订单",
    )
    sku = models.ForeignKey(
        "products.SKU",
        on_delete=models.CASCADE,
        related_name="order_items",
        verbose_name="SKU",
    )
    sku_code = models.CharField("SKU 编码", max_length=64)
    spu_name = models.CharField("商品名称", max_length=128)
    specs = models.JSONField("规格组合", default=dict, blank=True)
    main_image = models.CharField("商品图片", max_length=255, blank=True)
    price = models.DecimalField("单价", max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField("数量")
    subtotal = models.DecimalField("小计", max_digits=12, decimal_places=2)

    class Meta:
        db_table = "orders_order_item"
        verbose_name = "订单项"
        verbose_name_plural = "订单项"

    def __str__(self):
        return f"{self.spu_name} x {self.quantity}"
