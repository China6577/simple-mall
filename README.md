# SimpleMall - 企业级中型电商系统

前后端分离的电商学习项目，技术栈：Vue 3 + Django REST Framework + MySQL + Redis + RabbitMQ + Celery + Docker。

> 本项目为教学导向，代码注重清晰、正确与可学习性，避免过度工程化。

## 已完成功能

- **用户认证**：注册、登录、JWT Token（Access/Refresh）、Token 刷新、退出登录
- **商品模块**：SPU/SKU、分类、品牌、搜索、筛选、库存同步
- **购物车**：添加、修改数量、选中/取消、删除、同步登录态
- **订单模块**：创建订单、库存锁定、订单状态流转、超时自动取消
- **优惠券**：满减券、折扣券、领取、使用、叠加规则
- **支付模块**：模拟支付回调、支付记录
- **收货地址**：增删改查、默认地址
- **后台管理**：Django Admin 后台
- **异步任务**：Celery + RabbitMQ 处理订单超时、销量统计
- **部署与监控**：Docker Compose 开发/生产编排、健康检查、模拟数据
- **前端 UI**：Apple 风格极简设计、响应式布局

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router + Element Plus + SCSS |
| 后端 | Django 4.2 LTS + Django REST Framework + SimpleJWT + django-filter + drf-spectacular |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| 消息队列 | RabbitMQ 3 Management |
| 任务队列 | Celery + Celery Beat |
| 部署 | Docker + Docker Compose + Nginx |
| 测试 | pytest + Django Test |

## 快速启动（Docker Compose）

1. 复制环境变量：

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. 启动全部服务：

```bash
cd simple-mall
docker compose up -d --build
```

3. 访问：

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost |
| 后端 API | http://localhost/api/v1/ |
| API 文档 | http://localhost/api/docs/ |
| 健康检查 | http://localhost/api/v1/health/ |
| RabbitMQ 管理后台 | http://localhost:15672 （guest/guest） |

## 演示账号

启动时如设置 `DEMO_DATA=1`，会自动加载模拟数据：

| 角色 | 邮箱 | 密码 |
|------|------|------|
| 管理员 | admin@mall.local | admin123456 |
| 普通用户 | user1@mall.local | user123456 |
| 普通用户 | user2@mall.local | user123456 |

## 本地开发（不依赖 Docker）

### 后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python scripts/init_admin.py
python manage.py runserver
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问 http://localhost:5173，API 请求通过 Vite 代理到 http://localhost:8000。

## 数据库迁移

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

## 加载模拟数据

```bash
# Docker 环境
docker compose exec backend python manage.py seed_demo_data

# 本地环境
cd backend
python manage.py seed_demo_data
```

如需清空旧数据后重建：

```bash
python manage.py seed_demo_data --clean
```

## 测试

```bash
cd backend
pytest
```

当前后端测试覆盖：用户、商品、购物车、订单、优惠券、支付、库存、通用模块等。

## 项目结构

```text
simple-mall/
├── backend/                 # Django REST API
│   ├── apps/                # 业务应用
│   │   ├── users/           # 用户与认证
│   │   ├── products/        # 商品 SPU/SKU
│   │   ├── inventory/       # 库存
│   │   ├── carts/           # 购物车
│   │   ├── orders/          # 订单
│   │   ├── coupons/         # 优惠券
│   │   ├── payments/        # 支付
│   │   └── common/          # 通用工具、健康检查、模拟数据
│   ├── config/              # Django 全局配置
│   ├── requirements/        # Python 依赖
│   ├── scripts/             # 初始化脚本
│   ├── logs/                # 日志目录
│   ├── Dockerfile
│   └── .env.example
├── frontend/                # Vue 3 SPA
│   ├── src/
│   │   ├── api/             # 接口模块
│   │   ├── assets/          # 静态资源
│   │   ├── components/      # 可复用组件
│   │   ├── composables/     # 组合式函数
│   │   ├── layouts/         # 布局
│   │   ├── router/          # 路由
│   │   ├── stores/          # Pinia 状态
│   │   ├── utils/           # 工具函数
│   │   └── views/           # 页面
│   ├── Dockerfile
│   └── .env.example
├── nginx/                   # Nginx 配置
│   ├── nginx.conf           # 开发环境
│   └── nginx.prod.conf      # 生产环境
├── docker-compose.yml       # 开发环境编排
├── docker-compose.prod.yml  # 生产环境编排
├── .env.example
├── docs/                    # 阶段总结与使用文档
└── README.md
```

## 阶段说明

本项目按阶段迭代完成，完整历程见 `docs/` 目录：

- Phase 1：架构设计
- Phase 2：项目初始化与核心基础设施
- Phase 3：用户认证（JWT）
- Phase 4：商品 SPU/SKU 与库存
- Phase 5：购物车
- Phase 6：订单与库存锁定
- Phase 7：Celery 异步任务
- Phase 8：优惠券系统
- Phase 9：后台管理与数据看板
- Phase 10：Docker 部署、性能优化与模拟数据

Phase 10 为当前最后阶段，核心功能已全部实现。

## 下一步建议

- 接入真实支付网关（微信支付/支付宝）替换模拟支付
- 引入 Elasticsearch 实现商品搜索
- 增加秒杀/限时购模块
- 接入 Prometheus/Grafana 监控
- 补充端到端测试（Playwright/Cypress）

## 许可证

MIT License
