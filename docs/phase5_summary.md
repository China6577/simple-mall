# 阶段五：购物车模块

## 1. 本阶段目标

实现登录用户的购物车功能：

- 购物车数据持久化到 MySQL
- 添加/修改/删除/查询购物车商品
- 选中/取消选中及批量操作
- 库存校验、商品下架校验
- Redis 缓存购物车摘要，变更时失效
- 前端购物车页面、Header 购物车入口、商品详情页加入购物车

## 2. 设计思路

### 2.1 数据模型

- `CartItem` 以 `user + sku` 为唯一约束，每个用户对同一种 SKU 只有一条记录。
- 记录字段：数量 `quantity`、是否选中 `selected`。
- 价格、库存、商品状态不冗余，查询时通过关联实时获取，避免价格和库存变化后数据不一致。

### 2.2 库存与状态校验

- 添加/修改购物车时，校验 SKU 是否上架、SPU 是否上架、数量是否超过可售库存。
- 重复添加同一 SKU 时数量累加，但不超过当前可售库存。

### 2.3 Redis 摘要缓存

- 读取购物车时计算摘要（总件数、选中件数、选中金额）并缓存到 `cart:summary:{user_id}`，TTL 5 分钟。
- 增删改、批量选中操作后删除缓存，下次读取重新生成。

### 2.4 前端设计

- `CartStore` 集中管理购物车状态，登录后自动加载。
- 购物车页面展示商品列表、规格、单价、数量、小计、全选、合计。
- Header 显示购物车数量徽标。
- 商品详情页“加入购物车”调用真实接口。

## 3. 新增或修改的文件

### 后端

| 文件 | 说明 |
|------|------|
| `apps/carts/models.py` | `CartItem` 模型 |
| `apps/carts/serializers.py` | 购物车列表、创建、更新序列化器 |
| `apps/carts/views.py` | 购物车列表、添加、修改、删除、批量选中视图 |
| `apps/carts/urls.py` | 购物车模块路由 |
| `apps/carts/admin.py` | Django Admin 注册 |
| `apps/carts/services.py` | 摘要计算与 Redis 缓存辅助函数 |
| `apps/carts/tests.py` | 11 个购物车接口测试 |
| `apps/carts/migrations/0001_initial.py` | 购物车初始迁移 |
| `config/settings/test.py` | 测试环境移除 `django_ratelimit`，避免 LocMemCache 系统检查失败 |
| `config/urls.py` | 挂载 `api/v1/carts/` 路由 |

### 前端

| 文件 | 说明 |
|------|------|
| `src/api/cart.js` | 购物车 API 封装 |
| `src/stores/cart.js` | Pinia 购物车状态管理 |
| `src/views/cart/CartView.vue` | 购物车页面 |
| `src/components/AppHeader.vue` | 增加购物车入口与数量徽标 |
| `src/views/product/ProductDetailView.vue` | 接入真实加入购物车逻辑 |
| `src/router/index.js` | 添加 `/cart` 路由 |

## 4. 核心代码说明

### 4.1 购物车模型

```python
class CartItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, ...)
    sku = models.ForeignKey("products.SKU", ...)
    quantity = models.PositiveIntegerField("数量", default=1)
    selected = models.BooleanField("是否选中", default=True)

    class Meta:
        unique_together = [["user", "sku"]]
```

### 4.2 添加商品时数量累加

```python
def create(self, validated_data):
    item, created = CartItem.objects.get_or_create(
        user=user, sku=sku, defaults={"quantity": quantity, "selected": True}
    )
    if not created:
        available = sku.stock_record.available
        item.quantity = min(item.quantity + quantity, available)
        item.selected = True
        item.save(update_fields=["quantity", "selected", "updated_at"])
    return item
```

### 4.3 Redis 缓存失效

```python
from .services import delete_cart_summary_cache

def post(self, request):
    serializer.save()
    delete_cart_summary_cache(request.user.id)
    ...
```

### 4.4 前端购物车状态

```javascript
export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const summary = ref({ total_count: 0, selected_count: 0, total_amount: 0 })

  async function addToCart(skuId, quantity = 1) {
    await cartApi.addToCart({ sku_id: skuId, quantity })
    await loadCart()
  }

  return { items, summary, addToCart, ... }
})
```

## 5. API 列表

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `/api/v1/carts/` | 登录 | 查询购物车列表及摘要 |
| POST | `/api/v1/carts/items/` | 登录 | 添加商品（sku_id, quantity） |
| PUT | `/api/v1/carts/items/{id}/` | 登录 | 修改数量/选中状态 |
| DELETE | `/api/v1/carts/items/{id}/` | 登录 | 删除商品 |
| POST | `/api/v1/carts/select/` | 登录 | 批量选中/取消（item_ids, selected） |

## 6. 安装和运行命令

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

## 7. 数据库迁移命令

```bash
cd simple-mall/backend
python manage.py migrate
```

本阶段新增迁移：

- `apps/carts/migrations/0001_initial.py`

## 8. 测试命令

```bash
cd simple-mall/backend
python -m pytest apps/users/tests.py apps/products/tests.py apps/carts/tests.py -v --ds=config.settings.test
```

## 9. 测试结果

```text
33 passed in 5.70s
```

- 用户模块：15 个测试全部通过
- 商品模块：7 个测试全部通过
- 购物车模块：11 个测试全部通过

前端构建：`npm run build` ✅

## 10. 常见错误和排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `manage.py check` 报 `django_ratelimit.E003` | 测试环境使用 LocMemCache | 在 `test.py` 中移除 `django_ratelimit` |
| 购物车金额断言失败 `'18997.0' != '18997.00'` | Decimal JSON 序列化精度 | 测试中使用 `Decimal` 对象比较 |
| 前端构建报 `no-unused-vars` | CartView 引入未使用的 `router` | 删除无用导入 |
| 前端构建报 `vue/attributes-order` | 模板属性顺序不符合 ESLint | 调整 `@update:model-value` 到属性末尾 |
| 前端构建 safe-delete 失败 | `dist/` 目录被锁定 | 手动删除 `dist/` 后重新构建 |

## 11. 本阶段仍未实现

- 未登录游客购物车（需本地存储 + 登录后合并，本项目按需求暂不实现）
- 购物车商品失效/下架提示
- 订单结算（下一阶段实现）
- 优惠券在购物车中的计算

## 12. 下一阶段计划

**阶段六：订单与库存模块**

将实现：

- 从购物车选中商品创建订单
- 订单状态机（待支付、已支付、已发货、已完成、已取消）
- 库存锁定/释放/扣减
- 防超卖（select_for_update 行锁 + 乐观锁）
- 模拟支付与回调
- 前端订单确认页、订单列表、订单详情
