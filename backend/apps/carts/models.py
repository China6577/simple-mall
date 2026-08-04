"""购物车模块模型。

设计说明：
- 登录用户的购物车数据持久化在 MySQL，按用户 + SKU 唯一。
- 未登录用户不保留购物车（本项目暂不做游客购物车）。
- 购物车只记录 SKU、数量和选中状态；价格、库存以商品模块为准。
"""

from django.conf import settings
from django.db import models


class CartItem(models.Model):
    """购物车条目：一个用户同一种 SKU 只有一条记录。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="用户",
    )
    sku = models.ForeignKey(
        "products.SKU",
        on_delete=models.CASCADE,
        related_name="cart_items",
        verbose_name="SKU",
    )
    quantity = models.PositiveIntegerField("数量", default=1)
    selected = models.BooleanField("是否选中", default=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "carts_cart_item"
        verbose_name = "购物车商品"
        verbose_name_plural = "购物车商品"
        ordering = ["-created_at"]
        unique_together = [["user", "sku"]]

    def __str__(self):
        return f"{self.user.username} - {self.sku.sku_code} x {self.quantity}"
