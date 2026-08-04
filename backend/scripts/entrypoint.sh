#!/bin/sh
# 后端容器入口脚本：等待依赖就绪，然后执行容器启动命令。
# 数据库迁移、管理员创建、模拟数据加载请在各自的 docker-compose command 中显式控制，
# 避免 backend / celery-worker / celery-beat 多个容器并发执行迁移。

set -e

# 默认环境变量
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-config.settings.prod}
export DB_HOST=${DB_HOST:-mysql}
export DB_PORT=${DB_PORT:-3306}
export DB_USER=${DB_USER:-mall_user}
export DB_PASSWORD=${DB_PASSWORD:-mall_password}
export DB_NAME=${DB_NAME:-mall}

# 等待 MySQL 就绪
python scripts/wait_for_mysql.py

# 执行容器启动命令
exec "$@"
