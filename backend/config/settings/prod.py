"""生产环境配置。

本文件继承 base.py，关闭 DEBUG，启用安全增强、Whitenoise 静态文件服务、
数据库连接池等生产环境常用优化。
"""

from .base import *

DEBUG = False

# 生产环境必须显式配置允许的来源
CORS_ALLOW_ALL_ORIGINS = False

# 安全增强
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False").lower() in ("1", "true")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# 信任由 Nginx 转发的 HTTPS 请求
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 静态文件使用 Whitenoise 直接由 WSGI 应用提供，Nginx 可再前置缓存
INSTALLED_APPS = INSTALLED_APPS.copy()
INSTALLED_APPS.insert(0, "whitenoise.runserver_nostatic")

MIDDLEWARE = MIDDLEWARE.copy()
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# 数据库连接池：django-db-connection-pool 提供，默认保持 5 个连接
DATABASES["default"]["OPTIONS"] = {
    "charset": "utf8mb4",
    "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
    "pool": {
        "min_size": int(os.getenv("DB_POOL_MIN_SIZE", "2")),
        "max_size": int(os.getenv("DB_POOL_MAX_SIZE", "10")),
        "timeout": int(os.getenv("DB_POOL_TIMEOUT", "30")),
    },
}

# 日志只保留 WARNING 级别到控制台，减少磁盘 IO
LOGGING["handlers"]["console"]["level"] = "WARNING"
LOGGING["handlers"]["file"]["level"] = "INFO"

# 生产环境关闭 django-ratelimit 的系统检查，避免缓存后端不支持报错
# 实际限流仍通过 Redis 生效
RATELIMIT_ENABLE = True

# Gunicorn 等 WSGI 服务器通常不需要 request log middleware 重复输出
# 如需关闭可注释下面这行，但保留有利于排查问题
# MIDDLEWARE = [m for m in MIDDLEWARE if m != "apps.common.middleware.RequestLogMiddleware"]
