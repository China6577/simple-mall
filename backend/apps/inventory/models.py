"""库存模块模型。

库存设计采用"总库存 + 锁定库存"模式：
- quantity：仓库实际可用总库存。
- locked_quantity：已被订单锁定但尚未支付的库存。
- 可售库存 = quantity - locked_quantity。

创建订单时只锁定库存，支付成功后再真正扣减；
超时未支付或主动取消订单时释放锁定库存。

使用 version 字段做乐观锁，防止并发更新导致超卖。
"""

from django.conf import settings
from django.db import models


class Stock(models.Model):
    """SKU 库存主表，与 SKU 一对一关联。"""

    sku = models.OneToOneField(
        "products.SKU",
        on_delete=models.CASCADE,
        related_name="stock_record",
        verbose_name="SKU",
    )
    quantity = models.PositiveIntegerField("总库存", default=0)
    locked_quantity = models.PositiveIntegerField("锁定库存", default=0)
    # 乐观锁版本号，每次更新库存时递增
    version = models.PositiveIntegerField("版本号", default=0)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "inventory_stock"
        verbose_name = "SKU 库存"
        verbose_name_plural = "SKU 库存"

    def __str__(self):
        return f"{self.sku.sku_code}: 总{self.quantity} / 锁{self.locked_quantity}"

    @property
    def available(self):
        """可售库存 = 总库存 - 锁定库存。"""
        return self.quantity - self.locked_quantity


class StockLog(models.Model):
    """库存变更日志，用于审计和排查。"""

    OPER_TYPE_CHOICES = [
        ("init", "初始入库"),
        ("increase", "增加库存"),
        ("decrease", "扣减库存"),
        ("lock", "锁定库存"),
        ("unlock", "释放库存"),
        ("sale", "销售出库"),
    ]

    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name="logs",
        verbose_name="库存记录",
    )
    change_quantity = models.IntegerField("总库存变化量")
    locked_change = models.IntegerField("锁定库存变化量")
    available_after = models.IntegerField("变更后可售库存")
    reason = models.CharField("变更原因", max_length=128)
    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="操作人",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "inventory_stock_log"
        verbose_name = "库存变更日志"
        verbose_name_plural = "库存变更日志"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.stock.sku.sku_code} {self.reason} {self.change_quantity}"
