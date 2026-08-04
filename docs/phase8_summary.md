# Phase 8 总结：优惠券模块

## 本阶段目标

实现 SimpleMall 优惠券系统，支持：

1. 运营人员在后台创建满减券、折扣券。
2. 用户在领券中心领取优惠券。
3. 下单时选择多张优惠券叠加抵扣。
4. 取消订单时自动退回优惠券。

## 关键实现

### 1. 数据模型 `apps/coupons/models.py`

- `Coupon`：优惠券模板，包含券码、名称、类型（满减/折扣）、面值/折扣率、最低使用金额、最大抵扣金额、发行量/剩余量、每人限领、有效期、启用状态。
- `UserCoupon`：用户领取记录，包含状态（未使用/已使用/已过期）、领取/使用时间、关联订单。
- `OrderCoupon`：订单与优惠券的中间表，支持叠加使用，记录每张券的抵扣金额。

### 2. 业务服务 `apps/coupons/services.py`

- `claim_coupon(user, coupon_id)`：领取优惠券，使用 `select_for_update()` 防止并发超发，校验有效期、剩余量、每人限领。
- `list_available_user_coupons(user)`：查询用户当前可用优惠券。
- `validate_and_apply_coupons(user, user_coupon_ids, total_amount)`：
  - 校验优惠券是否属于用户、未使用、在有效期内。
  - 校验订单总金额是否满足每张券的最低使用门槛。
  - 叠加规则：**先应用折扣券，再应用满减券**，折扣券受 `max_discount_amount` 上限约束。
  - 返回总抵扣金额与抵扣明细。

### 3. 订单模块集成

- `apps/orders/services.py` 的 `create_order` 增加 `coupon_ids` 参数：
  - 创建订单前调用优惠券服务计算抵扣。
  - 事务中创建 `OrderCoupon` 记录并标记 `UserCoupon` 为已使用。
- `apps/orders/services.py` 的 `cancel_order`：
  - 取消订单时遍历 `order.order_coupons`，将关联的 `UserCoupon` 重置为未使用状态。
- `apps/orders/serializers.py`：
  - `OrderCreateSerializer` 增加 `coupon_ids` 字段。
  - 新增 `OrderCouponSerializer`，`OrderDetailSerializer` 增加 `coupons` 字段展示已使用券。
- `apps/orders/views.py`：创建订单时从请求数据读取 `coupon_ids` 并传入服务。

### 4. API 接口 `apps/coupons/views.py`

- `GET /api/v1/coupons/`：可领取优惠券列表。
- `GET /api/v1/coupons/my/`：我的优惠券列表，支持 `status` 筛选。
- `POST /api/v1/coupons/{id}/claim/`：领取优惠券。
- `POST /api/v1/coupons/calculate/`：优惠券试算。
- `GET /api/v1/coupons/available/?cart_item_ids=1,2`：查询购物车可用优惠券及抵扣金额。

### 5. 前端实现

- 新增 `src/api/coupon.js`：封装优惠券接口。
- 新增 `src/views/coupon/CouponCenterView.vue`：
  - 领券中心展示可领取的满减/折扣券。
  - “我的优惠券”标签页展示已领取券及状态。
- 更新 `src/views/order/OrderConfirmView.vue`：
  - 加载购物车可用优惠券列表。
  - 支持多选优惠券并实时试算抵扣金额。
  - 提交订单时携带 `coupon_ids`。
- 更新 `src/components/AppHeader.vue`：登录后显示“优惠券”入口。
- 更新 `src/router/index.js`：注册 `/coupons` 路由。

### 6. 后台管理 `apps/coupons/admin.py`

- 注册 `Coupon`、`UserCoupon`、`OrderCoupon`，支持按类型/状态筛选和搜索。

### 7. 测试新增

新增 `apps/coupons/tests.py`，覆盖：

- 可领取优惠券列表。
- 领取优惠券及每人限领校验。
- 折扣券 + 满减券叠加试算。
- 下单使用优惠券并扣减应付金额。
- 取消订单退回优惠券。
- 查询购物车可用优惠券。

## 验证结果

- `python manage.py makemigrations coupons orders --settings=config.settings.test` ✅
- `python manage.py check --settings=config.settings.test` ✅
- `pytest` 全量测试：**63 个全部通过** ✅
- `npm run build` 前端构建通过 ✅

## 下阶段

Phase 9：后台管理与数据看板（运营/管理员商品、订单、用户、优惠券管理，销量统计看板）。
