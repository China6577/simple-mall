"""库存模块信号处理器。

创建 SKU 时自动初始化库存记录，避免业务代码遗漏。
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.products.models import SKU

from .models import Stock


@receiver(post_save, sender=SKU)
def create_stock_for_sku(sender, instance, created, **kwargs):
    """SKU 首次创建时，自动创建对应库存记录。"""
    if created:
        Stock.objects.get_or_create(
            sku=instance,
            defaults={"quantity": instance.stock, "locked_quantity": 0},
        )
