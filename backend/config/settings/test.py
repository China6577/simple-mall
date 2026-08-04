"""测试环境配置。

本地运行测试时使用 SQLite 内存数据库，不依赖 MySQL/Redis/RabbitMQ。
"""

from .dev import *

# 测试环境允许任意 HOST，避免 APIClient 报 DisallowedHost
ALLOWED_HOSTS = ["*"]

# HS256 签名密钥至少 32 字节，测试环境使用固定长密钥
SECRET_KEY = "test-secret-key-at-least-32-bytes-long-for-jwt-signing"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# 测试时使用本地内存缓存，不依赖 Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# 测试时不发送真实邮件
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# 关闭限流，避免测试被拦截
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []

# 测试环境移除 django-ratelimit，避免 LocMemCache 不被支持导致 manage.py 失败
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "django_ratelimit"]

# Celery 同步执行，便于测试异步任务
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# 测试环境订单自动取消超时时间缩短为 1 秒，便于验证
ORDER_AUTO_CANCEL_SECONDS = 1
