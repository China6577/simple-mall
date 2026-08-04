# 阶段四：商品模块

## 1. 本阶段目标

实现商品体系的核心后端接口与前端页面：

- 商品分类（多级树形）
- 商品品牌
- SPU / SKU 数据模型与关系
- 商品图片与规格选项
- SKU 库存自动关联
- 商品列表、搜索、筛选、排序、分页
- 商品详情
- 热门商品接口
- 前端首页、商品列表页、商品详情页、搜索结果页

## 2. 设计思路

### 2.1 SPU / SKU 分离

- **SPU（Standard Product Unit）**：描述商品整体信息，如 "iPhone 15"，包含名称、分类、品牌、图文详情、主图等。
- **SKU（Stock Keeping Unit）**：描述可售卖的具体规格，如 "iPhone 15 / 黑色 / 128G"，包含价格、库存、销量、规格组合、上下架状态等。
- 一个 SPU 下可有多个 SKU，用户下单时选择的是 SKU。

### 2.2 库存与商品解耦

- 库存模型 `inventory.Stock` 独立存放，通过 `OneToOneField` 关联到 `products.SKU`。
- 创建 SKU 时通过 Django 信号自动创建库存记录，避免业务代码遗漏。
- SKU 上的 `stock` 字段是冗余展示字段，真实库存以 `inventory.Stock` 为准。

### 2.3 价格与金额

- 价格使用 `DecimalField(max_digits=12, decimal_places=2)`，避免浮点误差。
- 默认单位为人民币元。

### 2.4 列表查询

- 使用 `django-filter` 实现分类、品牌、价格区间筛选。
- 使用 DRF 内置 `SearchFilter` 实现关键词搜索（搜索 SPU 名称和简介）。
- 使用 DRF 内置 `OrderingFilter` 实现排序。
- 自定义分页器返回统一格式：`{ total, page, page_size, results }`。

## 3. 新增或修改的文件

### 后端

| 文件 | 说明 |
|------|------|
| `apps/products/models.py` | Category、Brand、SPU、SPUSpec、SpecOption、SKU、ProductImage 模型 |
| `apps/products/serializers.py` | 分类、品牌、规格、SKU、SPU 列表/详情序列化器 |
| `apps/products/filters.py` | SPUFilter：分类、品牌、价格区间筛选 |
| `apps/products/views.py` | CategoryListView、BrandListView、SPUListView、SPUDetailView、ProductHotView |
| `apps/products/urls.py` | 商品模块路由 |
| `apps/products/admin.py` | Django Admin 中 SPU/SKU/分类/品牌的注册与内联 |
| `apps/products/tests.py` | 7 个商品接口测试 |
| `apps/inventory/models.py` | Stock、StockLog 库存与库存变更日志 |
| `apps/inventory/admin.py` | 库存 Admin |
| `apps/inventory/apps.py` | ready() 中导入信号处理器 |
| `apps/inventory/signals.py` | SKU 创建时自动初始化库存记录 |
| `apps/inventory/migrations/0001_initial.py` | 库存初始迁移 |
| `apps/products/migrations/0001_initial.py` | 商品初始迁移 |
| `config/urls.py` | 挂载 `api/v1/products/` 路由 |

### 前端

| 文件 | 说明 |
|------|------|
| `src/api/product.js` | 增加品牌、热门商品接口 |
| `src/views/home/HomeView.vue` | 首页展示商品列表，适配统一响应格式 |
| `src/views/product/ProductListView.vue` | 商品列表页：分类/品牌/关键词/排序/分页 |
| `src/views/product/ProductDetailView.vue` | 商品详情页：规格选择、价格、库存、加入购物车 |
| `src/views/product/SearchResultView.vue` | 搜索结果页 |
| `src/router/index.js` | 添加商品列表、详情、搜索路由 |
| `src/components/AppHeader.vue` | 添加搜索框，支持跳转到搜索页 |

## 4. 核心代码说明

### 4.1 商品模型关系

```python
Category (self ForeignKey)  # 多级分类
Brand
SPU -> Category, Brand
SPUSpec -> SPU            # 规格名，如 "颜色"
SpecOption -> SPUSpec     # 规格选项，如 "红色"
SKU -> SPU                # 具体可售卖实体
ProductImage -> SPU/SKU   # 图片
Stock -> SKU (OneToOne)   # 库存
```

### 4.2 SKU 创建自动初始化库存

```python
# apps/inventory/signals.py
@receiver(post_save, sender=SKU)
def create_stock_for_sku(sender, instance, created, **kwargs):
    if created:
        Stock.objects.get_or_create(
            sku=instance,
            defaults={"quantity": instance.stock, "locked_quantity": 0},
        )
```

### 4.3 商品列表接口

`SPUListView` 使用 `DjangoFilterBackend`、`SearchFilter`、`OrderingFilter` 组合，支持：

- `?category=1` 按分类筛选
- `?brand=1` 按品牌筛选
- `?min_price=100&max_price=500` 价格区间
- `?keyword=iPhone` 关键词搜索
- `?ordering=-created_at` 排序
- `?hot=1` 热门（按 SKU 最大销量降序）
- `?new=1` 新品（最近 30 天）

### 4.4 统一响应与测试

DRF 测试客户端 `APIClient.response.data` 是渲染前的原始数据，因此商品测试使用 `json.loads(response.content)` 来验证统一包装后的响应格式 `{code, message, data}`。

## 5. 安装和运行命令

### 本地开发后端

```bash
cd simple-mall/backend
python manage.py migrate
python manage.py runserver
```

### 本地开发前端

```bash
cd simple-mall/frontend
npm run dev
```

### Docker Compose

```bash
cd simple-mall
docker-compose up -d --build
```

## 6. 数据库迁移命令

```bash
cd simple-mall/backend
python manage.py migrate
```

本阶段新增迁移：

- `apps/products/migrations/0001_initial.py`
- `apps/inventory/migrations/0001_initial.py`

## 7. 测试命令

```bash
cd simple-mall/backend
python -m pytest apps/users/tests.py apps/products/tests.py -v --ds=config.settings.test
```

## 8. 测试结果

```text
22 passed in 3.76s
```

- 用户模块：15 个测试全部通过
- 商品模块：7 个测试全部通过

## 9. 常见错误和排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `Model class products.models.Category doesn't declare an explicit app_label` | pytest 收集阶段 Django 未 setup | 将模型导入放到 `setUp()` 中 |
| 详情接口返回 500 `Expected view ... named "id"` | `lookup_field` 与 URL 参数名不一致 | 使用默认 `pk` 或保持 URL 与 `lookup_field` 一致 |
| 列表测试 `KeyError: 'count'` | 分页器返回字段名为 `total` | 测试中使用 `total` |
| 前端构建 safe-delete 失败 | `dist/` 目录被锁定 | 手动删除 `dist/` 后重新构建 |

## 10. 本阶段仍未实现

- 商品收藏
- 商品评价
- 商品上下架后台管理完整功能
- 图片实际上传（目前为 ImageField 占位）
- 购物车、订单、优惠券等业务模块

## 11. 下一阶段计划

**阶段五：购物车模块**

将实现：

- 登录用户购物车数据库存储
- Redis 缓存购物车摘要
- 添加/修改/删除/选择购物车商品
- 处理商品下架、库存不足、价格变化
- 前端购物车页面
