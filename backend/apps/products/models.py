"""商品模块模型。

核心概念：
- SPU（Standard Product Unit，标准产品单位）：描述一款商品的整体信息，
  如 "iPhone 15"，包含名称、分类、品牌、图文详情等。
- SKU（Stock Keeping Unit，库存量单位）：描述一款商品下可售卖的具体规格，
  如 "iPhone 15 / 128G / 黑色"，包含价格、库存、规格组合等。

举例：
- SPU：iPhone 15
  - 规格 1：颜色（黑、白、蓝）
  - 规格 2：存储容量（128G、256G）
- SKU：iPhone 15 + 黑色 + 128G，这是一个可下单购买的实体。
"""

from django.core.validators import MinValueValidator
from django.db import models


class BaseModel(models.Model):
    """公共基础字段：创建时间和更新时间。"""

    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        abstract = True


class Category(BaseModel):
    """商品分类，支持多级（树形结构）。"""

    name = models.CharField("分类名称", max_length=64)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        verbose_name="父分类",
        null=True,
        blank=True,
    )
    # level 用于快速区分一级/二级/三级分类，避免递归计算层级
    level = models.PositiveSmallIntegerField("层级", default=1)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "products_category"
        verbose_name = "商品分类"
        verbose_name_plural = "商品分类"
        ordering = ["sort_order", "-created_at"]

    def __str__(self):
        return self.name


class Brand(BaseModel):
    """商品品牌。"""

    name = models.CharField("品牌名称", max_length=64, unique=True)
    logo = models.ImageField("品牌 Logo", upload_to="brands/", blank=True)
    description = models.TextField("品牌介绍", blank=True)
    is_active = models.BooleanField("是否启用", default=True)

    class Meta:
        db_table = "products_brand"
        verbose_name = "品牌"
        verbose_name_plural = "品牌"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SPU(BaseModel):
    """标准产品单位：描述商品整体信息。"""

    spu_code = models.CharField("SPU 编码", max_length=64, unique=True, db_index=True)
    name = models.CharField("商品名称", max_length=128)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="spus",
        verbose_name="所属分类",
    )
    brand = models.ForeignKey(
        Brand,
        on_delete=models.SET_NULL,
        related_name="spus",
        verbose_name="品牌",
        null=True,
        blank=True,
    )
    description = models.TextField("商品简介", blank=True)
    main_image = models.ImageField("主图", upload_to="products/spu/")
    detail = models.TextField("商品详情（支持 HTML）", blank=True)
    is_active = models.BooleanField("是否上架", default=True)

    class Meta:
        db_table = "products_spu"
        verbose_name = "SPU"
        verbose_name_plural = "SPU"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class SPUSpec(BaseModel):
    """SPU 规格名：如 "颜色"、"尺码"。"""

    spu = models.ForeignKey(
        SPU,
        on_delete=models.CASCADE,
        related_name="specs",
        verbose_name="所属 SPU",
    )
    name = models.CharField("规格名称", max_length=32)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)

    class Meta:
        db_table = "products_spu_spec"
        verbose_name = "SPU 规格"
        verbose_name_plural = "SPU 规格"
        ordering = ["sort_order", "id"]
        unique_together = [["spu", "name"]]

    def __str__(self):
        return f"{self.spu.name} - {self.name}"


class SpecOption(BaseModel):
    """规格选项：如 "红色"、"XL"。"""

    spec = models.ForeignKey(
        SPUSpec,
        on_delete=models.CASCADE,
        related_name="options",
        verbose_name="所属规格",
    )
    value = models.CharField("选项值", max_length=32)
    sort_order = models.PositiveSmallIntegerField("排序", default=0)

    class Meta:
        db_table = "products_spec_option"
        verbose_name = "规格选项"
        verbose_name_plural = "规格选项"
        ordering = ["sort_order", "id"]
        unique_together = [["spec", "value"]]

    def __str__(self):
        return f"{self.spec.name}: {self.value}"


class SKU(BaseModel):
    """库存量单位：可售卖的商品实体。"""

    sku_code = models.CharField("SKU 编码", max_length=64, unique=True, db_index=True)
    spu = models.ForeignKey(
        SPU,
        on_delete=models.CASCADE,
        related_name="skus",
        verbose_name="所属 SPU",
    )
    # 金额使用 DecimalField，避免浮点误差；单位为元
    price = models.DecimalField(
        "售价",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    cost_price = models.DecimalField(
        "成本价",
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
    )
    # stock 是冗余字段，实际以 inventory.Stock 为准，用于列表快速展示
    stock = models.PositiveIntegerField("库存数量", default=0)
    sales = models.PositiveIntegerField("销量", default=0)
    status = models.BooleanField("是否上架", default=True)
    is_default = models.BooleanField("是否默认 SKU", default=False)
    # specs 保存 {"颜色": "红色", "尺码": "XL"}，方便前端展示和订单快照
    specs = models.JSONField("规格组合", default=dict, blank=True)

    class Meta:
        db_table = "products_sku"
        verbose_name = "SKU"
        verbose_name_plural = "SKU"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.spu.name} ({self.sku_code})"


class ProductImage(BaseModel):
    """商品图片：既可以属于 SPU（详情图），也可以属于 SKU（SKU 图）。"""

    spu = models.ForeignKey(
        SPU,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="所属 SPU",
        null=True,
        blank=True,
    )
    sku = models.ForeignKey(
        SKU,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="所属 SKU",
        null=True,
        blank=True,
    )
    image = models.ImageField("图片", upload_to="products/images/")
    sort_order = models.PositiveSmallIntegerField("排序", default=0)

    class Meta:
        db_table = "products_product_image"
        verbose_name = "商品图片"
        verbose_name_plural = "商品图片"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"图片 {self.id}"
