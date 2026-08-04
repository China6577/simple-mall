# 后端镜像：基于 Python 3.11 slim，非 root 用户运行
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 安装系统依赖（mysqlclient 需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# 先复制依赖并安装，利用 Docker 缓存层
COPY requirements/ /app/requirements/
RUN pip install -r /app/requirements/prod.txt

# 创建非 root 用户运行应用
RUN groupadd -r mall && useradd -r -g mall mall

# 复制项目代码
COPY . /app/

# 创建静态文件、媒体文件、日志目录并修改属主
RUN mkdir -p /app/staticfiles /app/media /app/logs && \
    chown -R mall:mall /app

# 收集静态文件（生产环境使用 whitenoise 或 Nginx 提供）
RUN python manage.py collectstatic --noinput

# 默认入口脚本：等待数据库、执行迁移、创建管理员、启动 Gunicorn
COPY scripts/entrypoint.sh /app/scripts/entrypoint.sh
RUN chmod +x /app/scripts/entrypoint.sh

USER mall

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "-b", "0.0.0.0:8000", "-w", "4", "--access-logfile", "-", "--error-logfile", "-"]
