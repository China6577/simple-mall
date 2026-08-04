"""通用抽象模型。"""

from django.db import models


class BaseModel(models.Model):
    """
    所有业务模型的抽象基类，提供统一的创建和更新时间。

    该模型不会单独生成数据表，只作为其他模型的父类使用。
    """

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
