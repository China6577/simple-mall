# Phase 7 总结：Celery 异步任务

## 本阶段目标

为 SimpleMall 引入 Celery 异步任务处理机制，实现：

1. 订单超时自动取消并释放库存。
2. 支付成功后异步发送邮件通知。
3. 低库存预警扫描。
4. 商品销量与分类销量统计刷新。

## 关键实现

### 1. 邮件工具 `apps/common/mail.py`

- 封装 `send_templated_email`，统一调用 Django `send_mail`。
- 开发/测试环境通过 `EMAIL_BACKEND` 输出到控制台或内存，不依赖 SMTP。

### 2. 订单任务 `apps/orders/tasks.py`

- `auto_cancel_pending_order(order_id)`
  - 创建订单后通过 `apply_async(countdown=ORDER_AUTO_CANCEL_SECONDS)` 延迟调度。
  - 任务内部二次校验订单是否已超时，避免任务被提前执行（如 Celery eager 模式）。
  - 仅对仍处于 `pending_payment` 状态的订单调用 `cancel_order` 释放库存。
- `scan_and_cancel_overdue_orders()`
  - 由 Celery Beat 每 5 分钟调度一次，作为兜底扫描。
  - 批量将超过 `ORDER_AUTO_CANCEL_SECONDS` 未支付的订单加入取消队列。
- `send_order_paid_email(order_id)`
  - 支付成功后异步发送邮件，包含订单号、金额、商品明细。

### 3. 商品任务 `apps/products/tasks.py`

- `check_low_stock_and_alert(threshold=10)`
  - 扫描可售库存低于阈值的 SKU，输出预警日志/控制台。
  - 使用 Redis 缓存控制 1 小时内不重复告警。
- `refresh_product_sales_stats()`
  - 聚合已支付/已发货/已完成订单的 SKU 销量。
  - 批量更新 `SKU.sales`，并将 SPU/分类销量写入 Redis 缓存，供首页排行榜使用。

### 4. 业务触发点

- `apps/orders/services.py`：订单创建成功后，在事务外调用 `auto_cancel_pending_order.apply_async`。
- `apps/payments/services.py`：支付回调成功后，在事务外调用 `send_order_paid_email.delay`。

### 5. 定时调度配置 `config/settings/base.py`

```python
CELERY_BEAT_SCHEDULE = {
    "scan-overdue-orders": {
        "task": "apps.orders.tasks.scan_and_cancel_overdue_orders",
        "schedule": timedelta(minutes=5),
    },
    "check-low-stock": {
        "task": "apps.products.tasks.check_low_stock_and_alert",
        "schedule": timedelta(hours=1),
        "kwargs": {"threshold": 10},
    },
    "refresh-product-sales-stats": {
        "task": "apps.products.tasks.refresh_product_sales_stats",
        "schedule": timedelta(minutes=30),
    },
}
```

同时新增环境变量 `ORDER_AUTO_CANCEL_SECONDS`（默认 1800 秒，测试环境 1 秒）。

### 6. 测试环境配置 `config/settings/test.py`

- `CELERY_TASK_ALWAYS_EAGER = True` 保持同步执行，便于测试。
- `ORDER_AUTO_CANCEL_SECONDS = 1` 缩短超时时间，便于验证自动取消逻辑。

### 7. 测试新增

新增测试文件：

- `apps/orders/test_tasks.py`：覆盖自动取消（未超时跳过/超时取消）、支付邮件、兜底扫描。
- `apps/products/test_tasks.py`：覆盖低库存预警、销量统计刷新。

## 验证结果

- `python manage.py check --settings=config.settings.test` ✅
- `pytest` 全量测试：56 个全部通过 ✅
- `npm run build` 前端构建通过 ✅

## 下阶段

Phase 8：优惠券模块（满减/折扣、可叠加、领取与使用）。
