# Phase 9 总结：后台管理与数据看板

## 本阶段目标

实现 SimpleMall 独立后台管理前端 + 管理 API，支持管理员/运营人员进行：

1. 商品 SPU/SKU 的查询、新增、编辑、删除。
2. 订单列表查询与状态查看。
3. 用户列表查询、角色与启用状态调整。
4. 优惠券模板的增删改查。
5. 数据看板：核心经营指标、近期订单、热销 SKU。

## 关键实现

### 1. 后端管理接口 `apps/admin_api/`

- 新增独立应用 `admin_api`，不引入新模型，聚合各业务模块的管理能力。
- 统一挂载到 `/api/v1/admin/`，权限使用 `IsAuthenticated + IsAdmin`。
- 序列化器：
  - `AdminSPUListSerializer` / `AdminSPUDetailSerializer` / `AdminSPUCreateUpdateSerializer`
  - `AdminSKUListSerializer` / `AdminSKUCreateUpdateSerializer`
  - `AdminOrderListSerializer`
  - `AdminUserListSerializer` / `AdminUserUpdateSerializer`
  - `AdminCouponSerializer`
- 视图接口：
  - `GET /api/v1/admin/dashboard/`：看板数据
  - `GET/POST /api/v1/admin/products/`：SPU 列表/创建
  - `GET/PUT/DELETE /api/v1/admin/products/{id}/`：SPU 详情/更新/删除
  - `GET/POST /api/v1/admin/skus/`：SKU 列表/创建
  - `GET/PUT/DELETE /api/v1/admin/skus/{id}/`：SKU 详情/更新/删除
  - `GET /api/v1/admin/orders/`：订单列表
  - `GET /api/v1/admin/users/`：用户列表
  - `GET/PATCH /api/v1/admin/users/{id}/`：用户详情/更新
  - `GET/POST /api/v1/admin/coupons/`：优惠券列表/创建
  - `GET/PUT/DELETE /api/v1/admin/coupons/{id}/`：优惠券详情/更新/删除

### 2. 数据看板

`DashboardView` 聚合以下指标：

- 注册用户数、商品 SPU 数、订单总数、待支付订单数
- 累计销售额、今日订单数、今日销售额
- 最近 10 笔订单
- 销量 TOP10 SKU

### 3. 前端管理后台

- 新增 `src/layouts/AdminLayout.vue`：侧边栏菜单 + 退出登录。
- 新增 `src/views/admin/`：
  - `DashboardView.vue`：数据看板
  - `ProductManageView.vue`：商品与 SKU 管理
  - `OrderManageView.vue`：订单管理
  - `UserManageView.vue`：用户管理
  - `CouponManageView.vue`：优惠券管理
- 新增 `src/api/admin.js`：封装后台管理接口。
- 更新 `src/router/index.js`：注册 `/admin/*` 路由，并增加管理员角色守卫。
- 更新 `src/components/AppHeader.vue`：管理员登录后显示“后台管理”入口。
- 更新 `src/utils/request.js`：上传文件时让浏览器自动设置 `Content-Type`（含 boundary）。

## 验证结果

- `python manage.py check --settings=config.settings.test` ✅
- `pytest` 全量测试：**70 个全部通过** ✅
- `npm run build` 前端构建通过 ✅

## 下阶段

Phase 10：Docker 部署与性能优化（多环境配置、Nginx、Docker Compose、Gunicorn、静态文件、健康检查完善）。
