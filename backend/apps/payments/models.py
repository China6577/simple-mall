"""支付模块模型。"""

from django.db import models


class PaymentRecord(models.Model):
    """支付记录。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待支付"
        SUCCESS = "success", "支付成功"
        FAILED = "failed", "支付失败"

    order = models.ForeignKey(
        "orders.Order",
        on_delete=models.CASCADE,
        related_name="payment_records",
        verbose_name="订单",
    )
    payment_no = models.CharField("支付流水号", max_length=64, unique=True, db_index=True)
    amount = models.DecimalField("支付金额", max_digits=12, decimal_places=2)
    status = models.CharField(
        "状态",
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESS,
    )
    paid_at = models.DateTimeField("支付时间", null=True, blank=True)
    callback_data = models.JSONField("回调原始数据", default=dict, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "payments_payment_record"
        verbose_name = "支付记录"
        verbose_name_plural = "支付记录"
        ordering = ["-created_at"]

    def __str__(self):
        return self.payment_no
