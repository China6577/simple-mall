# 阶段六：订单与库存模块

## 1. 本阶段目标

实现订单全生命周期与库存一致性：

- 从购物车选中商品创建订单
- 订单状态机（待支付、已支付、已发货、已完成、已取消）
- 库存锁定/释放/扣减，防止超卖
- 模拟支付与幂等回调
- 前端订单确认页、订单列表、订单详情

## 2. 设计思路

### 2.1 订单与订单项

- `Order` 保存订单主信息、金额、地址快照、状态、时间戳。
- `OrderItem` 保存下单瞬间的 SKU 快照（编码、名称、规格、单价、数量、小计），避免商品后续修改影响历史订单。
- `Order.idempotency_key` 配合 Redis 锁防止重复提交。

### 2.2 库存三阶段

- **锁定**：创建订单时通过 `select_for_update()` 锁定 `Stock` 行，增加 `locked_quantity`。
- **释放**：取消订单时减少 `locked_quantity`。
- **扣减**：支付成功后同时减少 `quantity` 与 `locked_quantity`。
- 所有库存操作均记录 `StockLog`。

### 2.3 防超卖

- 行锁让同一 SKU 的并发订单串行化。
- 校验 `available = quantity - locked_quantity` 是否足够。
- 按 SKU ID 排序后加锁，避免死锁。

### 2.4 支付幂等

- `PaymentRecord` 使用唯一 `payment_no`。
- 回调处理时先用 `select_for_update()` 锁定订单。
- 已支付订单直接返回原记录，不做二次修改。
- 金额不匹配或流水号已存在则拒绝。

### 2.5 前端设计

- 购物车“去结算”携带选中条目 ID 到订单确认页。
- 确认页展示收货地址、商品清单、金额汇总，提交订单。
- 订单列表支持分页、支付、取消。
- 订单详情展示状态进度、商品、金额及操作按钮。

## 3. 新增或修改的文件

### 后端

| 文件 | 说明 |
|------|------|
| `apps/orders/models.py` | `Order`、`OrderItem` 模型 |
| `apps/orders/services.py` | 订单创建、取消、发货、确认收货服务 |
| `apps/orders/serializers.py` | 订单创建、列表、详情序列化器 |
| `apps/orders/views.py` | 订单列表/创建、详情、取消、支付、发货、确认收货视图 |
| `apps/orders/urls.py` | 订单模块路由 |
| `apps/orders/admin.py` | Django Admin 注册 |
| `apps/orders/tests.py` | 17 个订单接口测试 |
| `apps/orders/migrations/0001_initial.py` | 订单初始迁移 |
| `apps/payments/models.py` | `PaymentRecord` 支付记录模型 |
| `apps/payments/services.py` | 模拟支付、回调处理（幂等） |
| `apps/payments/views.py` | 模拟支付回调视图 |
| `apps/payments/urls.py` | 支付模块路由 |
| `apps/payments/admin.py` | 支付记录 Admin |
| `apps/payments/migrations/0001_initial.py` | 支付记录初始迁移 |
| `apps/inventory/services.py` | 库存锁定、释放、扣减服务 |
| `config/urls.py` | 挂载 `api/v1/orders/`、`api/v1/payments/` 路由 |

### 前端

| 文件 | 说明 |
|------|------|
| `src/api/order.js` | 订单 API 封装 |
| `src/api/user.js` | 增加收货地址接口 |
| `src/views/order/OrderConfirmView.vue` | 订单确认页 |
| `src/views/order/OrderListView.vue` | 订单列表页 |
| `src/views/order/OrderDetailView.vue` | 订单详情页 |
| `src/router/index.js` | 添加订单相关路由 |
| `src/views/cart/CartView.vue` | 去结算跳转订单确认页 |
| `src/components/AppHeader.vue` | 增加“我的订单”入口 |

## 4. 核心代码说明

### 4.1 库存锁定

```python
def lock_stock(sku_id, quantity, reason, operator=None):
    with transaction.atomic():
        stock = Stock.objects.select_for_update().get(sku_id=sku_id)
        if stock.available < quantity:
            raise BusinessException("库存不足")
        stock.locked_quantity += quantity
        stock.version += 1
        stock.save(update_fields=["locked_quantity", "version", "updated_at"])
        _create_stock_log(stock, 0, quantity, reason, operator)
        return stock
```

### 4.2 创建订单

```python
def create_order(user, cart_item_ids, address_id, remark="", idempotency_key=""):
    # 校验购物车条目、地址...
    sorted_items = sorted(cart_items, key=lambda x: x.sku_id)
    with transaction.atomic():
        if idempotency_key:
            if Order.objects.filter(user=user, idempotency_key=idempotency_key).exists():
                raise ConflictException("订单已提交，请勿重复操作")
        order = Order.objects.create(...)
        for item in sorted_items:
            lock_stock(item.sku_id, item.quantity, f"订单 {order.order_no} 创建", user)
            OrderItem.objects.create(order=order, sku=item.sku, ...)
        CartItem.objects.filter(id__in=cart_item_ids).delete()
    return order
```

### 4.3 支付回调幂等

```python
def process_payment_callback(order_no, payment_no, amount, callback_data=None):
    with transaction.atomic():
        order = Order.objects.select_for_update().get(order_no=order_no)
        if order.status == Order.Status.PAID:
            return PaymentRecord.objects.filter(order=order).first()
        if PaymentRecord.objects.filter(payment_no=payment_no).exists():
            raise BusinessException("支付流水已处理")
        # 扣减库存、更新订单、创建支付记录
```

### 4.4 前端提交订单

```javascript
const idempotencyKey = `order-${Date.now()}-${Math.random().toString(36).slice(2)}`
const data = await orderApi.createOrder({
  cart_item_ids: cartItemIds.value,
  address_id: selectedAddressId.value,
  remark: remark.value,
  idempotency_key: idempotencyKey
})
router.push(`/orders/${data.order_no}`)
```

## 5. API 列表

### 订单

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/v1/orders/` | 登录 | 创建订单 |
| GET | `/api/v1/orders/` | 登录 | 订单列表 |
| GET | `/api/v1/orders/{order_no}/` | 登录 | 订单详情 |
| POST | `/api/v1/orders/{order_no}/cancel/` | 登录 | 取消订单 |
| POST | `/api/v1/orders/{order_no}/pay/` | 登录 | 模拟支付 |
| POST | `/api/v1/orders/{order_no}/ship/` | 运营/管理员 | 发货 |
| POST | `/api/v1/orders/{order_no}/confirm/` | 登录 | 确认收货 |

### 支付

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| POST | `/api/v1/payments/callback/` | 登录 | 模拟支付回调 |

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

- `apps/orders/migrations/0001_initial.py`
- `apps/payments/migrations/0001_initial.py`

## 8. 测试命令

```bash
cd simple-mall/backend
python -m pytest apps/users/tests.py apps/products/tests.py apps/carts/tests.py apps/orders/tests.py -v --ds=config.settings.test
```

## 9. 测试结果

```text
50 passed in 9.72s
```

- 用户模块：15 个测试全部通过
- 商品模块：7 个测试全部通过
- 购物车模块：11 个测试全部通过
- 订单模块：17 个测试全部通过

前端构建：`npm run build` ✅

## 10. 常见错误和排查

| 现象 | 原因 | 解决 |
|------|------|------|
| `NameError: name 'Order' is not defined` | payments/services.py 未导入 Order | 补充 `from apps.orders.models import Order` |
| `Field name 'status_display' is not valid` | OrderListSerializer 未声明 SerializerMethodField | 添加 `status_display = serializers.SerializerMethodField()` |
| `orders.Order.coupon` 关系错误 | coupons.UserCoupon 模型不存在 | 阶段八再实现优惠券，本阶段注释该字段 |
| 前端构建 `vue/attributes-order` | `v-if` 位置在 `class` 之后 | 调整 `v-if` 到属性最前面 |
| 前端构建 safe-delete 失败 | `dist/` 目录被锁定 | 手动删除 `dist/` 后重新构建 |

## 11. 本阶段仍未实现

- 订单超时自动取消（Celery 任务，阶段七）
- 运费计算
- 优惠券抵扣
- 退款/退货流程
- 真实支付网关对接
- 订单搜索与筛选

## 12. 下一阶段计划

**阶段七：Celery 异步任务**

将实现：

- 注册/支付邮件通知
- 订单超时自动取消
- 库存释放任务
- 销量与热门商品统计刷新
- 管理员操作日志异步写入
