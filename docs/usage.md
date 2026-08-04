# SimpleMall 部署与使用指南

本文档介绍如何本地/服务器部署 SimpleMall，以及如何使用内置的模拟数据快速体验系统功能。

## 目录

1. [环境要求](#环境要求)
2. [快速启动（开发环境）](#快速启动开发环境)
3. [生产环境部署](#生产环境部署)
4. [模拟数据说明](#模拟数据说明)
5. [常用命令](#常用命令)
6. [访问地址](#访问地址)

---

## 环境要求

- Docker >= 24.0
- Docker Compose >= 2.20
- （可选）Git

项目根目录为 `simple-mall/`，所有命令默认在该目录下执行。

---

## 快速启动（开发环境）

### 1. 配置环境变量

```bash
cp .env.example .env
```

`.env` 已包含开发环境的默认值，通常无需修改即可启动。

### 2. 启动全部服务

```bash
docker compose up -d
```

首次启动会：

1. 拉取 MySQL、Redis、RabbitMQ、Nginx 镜像。
2. 构建后端镜像并安装依赖。
3. 等待数据库就绪后自动执行 `migrate`。
4. 创建默认管理员账号。
5. 如果 `.env` 中 `DEMO_DATA=1`，则自动加载模拟数据。
6. 启动前端开发服务器（Vite HMR）。
7. 启动 Celery Worker 与 Beat。

### 3. 查看日志

```bash
# 全部服务
docker compose logs -f

# 仅后端
docker compose logs -f backend

# 仅 Celery Worker
docker compose logs -f celery-worker
```

### 4. 停止服务

```bash
docker compose down
```

如需清空数据库与缓存数据：

```bash
docker compose down -v
```

---

## 生产环境部署

### 1. 准备环境变量

```bash
cp .env.example .env
```

生产环境必须修改：

- `DJANGO_SECRET_KEY`：使用足够强度的随机字符串。
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`：你的域名，例如 `mall.example.com`
- `DB_PASSWORD`、`DB_ROOT_PASSWORD`、`RABBITMQ_PASSWORD`：使用强密码。
- `SECURE_SSL_REDIRECT=True`（如果启用了 HTTPS）
- `DEMO_DATA=0`（生产环境不建议加载演示数据）

### 2. 启动生产服务

```bash
docker compose -f docker-compose.prod.yml up -d
```

生产环境特点：

- 前端镜像会执行 `npm run build`，最终由 Nginx 托管静态文件。
- 后端使用 Gunicorn + Whitenoise 提供静态文件。
- Nginx 提供统一入口、静态资源缓存、健康检查代理。
- 所有服务都配置了自动重启与依赖健康检查。

### 3. 健康检查

```bash
curl http://localhost/health/
```

正常返回：

```json
{"status": "ok", "checks": {"database": "ok", "redis": "ok"}}
```

---

## 模拟数据说明

项目内置一个 Django management command，用于一键生成教学演示数据。

### 自动生成（推荐）

只要 `.env` 中设置 `DEMO_DATA=1`，Docker 启动时会自动执行：

```bash
python manage.py seed_demo_data
```

### 手动执行

进入后端容器：

```bash
docker compose exec backend python manage.py seed_demo_data
```

如需清空旧数据后重建：

```bash
docker compose exec backend python manage.py seed_demo_data --clean
```

### 演示数据内容

| 数据 | 数量 | 说明 |
|------|------|------|
| 管理员 | 1 | 账号 `admin`，密码 `admin123456` |
| 普通用户 | 2 | `user1@mall.local` / `user2@mall.local`，密码 `user123456` |
| 商品分类 | 4 | 手机通讯、电脑办公、智能穿戴、数码配件 |
| 品牌 | 3 | TechPro、BlueSky、GreenLife |
| SPU | 3 | 手机、笔记本、智能手表 |
| SKU | 5 | 不同颜色/内存/配置组合 |
| 优惠券 | 3 | 新用户满减券、满500减50、9折通用券 |
| 用户优惠券 | 6 | 每个普通用户领取全部 3 张券 |
| 购物车条目 | 3 | 演示选中/未选中状态 |
| 订单 | 2 | 一个已支付、一个待支付 |

### 登录体验

打开首页 `http://localhost/`，点击右上角“登录”：

- 管理员：
  - 邮箱：`admin@mall.local`
  - 密码：`admin123456`
  - 登录后 Header 会出现“后台管理”入口。
- 普通用户：
  - 邮箱：`user1@mall.local`
  - 密码：`user123456`
  - 可体验购物车、下单、优惠券、订单列表。

---

## 常用命令

### 后端

```bash
# 进入后端容器
docker compose exec backend sh

# 执行迁移
python manage.py migrate

# 创建超级管理员（已自动完成）
python manage.py createsuperuser

# 加载模拟数据
python manage.py seed_demo_data

# 运行测试
python -m pytest

# 查看 API 文档（Swagger）
# 开发环境：http://localhost/api/docs/
# 生产环境：http://your-domain/api/docs/
```

### Celery

```bash
# 手动触发一次超时订单扫描（进入后端容器）
celery -A config call apps.orders.tasks.scan_and_cancel_overdue_orders

# 刷新销量统计
celery -A config call apps.products.tasks.refresh_product_sales_stats
```

### 数据库

```bash
# 进入 MySQL 容器
docker compose exec mysql mysql -u mall_user -p mall
```

### 前端

```bash
# 进入前端容器
docker compose exec frontend sh

# 本地开发（非 Docker）
cd frontend
npm install
npm run dev
```

---

## 访问地址

### 开发环境

| 服务 | 地址 | 说明 |
|------|------|------|
| 统一入口（Nginx） | http://localhost/ | 前端 + API |
| 前端开发服务器 | http://localhost:5173/ | Vite HMR |
| 后端 API | http://localhost:8000/ | Django 开发服务器 |
| API 文档 | http://localhost/api/docs/ | Swagger UI |
| RabbitMQ 管理后台 | http://localhost:15672/ | guest/guest |
| 健康检查 | http://localhost/api/v1/health/ | 数据库 + Redis |

### 生产环境

| 服务 | 地址 | 说明 |
|------|------|------|
| 统一入口（Nginx） | http://localhost/ | 前端静态文件 + API 反向代理 |
| API 文档 | http://localhost/api/docs/ | Swagger UI |
| 健康检查 | http://localhost/health/ | 数据库 + Redis |

---

## 注意事项

1. **首次启动较慢**：MySQL 初始化、镜像构建、npm install 都需要时间，请耐心等待。
2. **内存建议**：开发环境至少 4 GB 内存；生产环境根据并发量调整 Gunicorn worker 数量。
3. **端口冲突**：如果本地已占用 80/3306/6379/5672/15672/5173/8000 端口，请修改 `.env` 或 `docker-compose.yml` 中的端口映射。
4. **生产 SSL**：本项目的 Nginx 配置未包含 HTTPS 证书。生产环境建议在 Nginx 前再挂一层反向代理（如 Nginx / Traefik / Cloudflare）处理 TLS。
5. **敏感信息**：切勿将 `.env` 文件提交到版本控制，已加入 `.gitignore`。
