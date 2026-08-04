"""开发环境配置。"""

from .base import *

DEBUG = True

# 开发环境允许所有来源，生产环境必须在 base 中严格限制
CORS_ALLOW_ALL_ORIGINS = True

# 开发环境日志级别更低，方便调试；容器开发环境只输出到控制台，避免 bind mount 后日志目录权限问题
LOGGING["handlers"] = {
    "console": {
        "level": "DEBUG",
        "class": "logging.StreamHandler",
        "formatter": "standard",
        "filters": ["sensitive"],
    }
}
LOGGING["root"]["handlers"] = ["console"]
LOGGING["loggers"]["django"]["handlers"] = ["console"]
LOGGING["loggers"]["django.request"]["handlers"] = ["console"]
LOGGING["loggers"]["celery"]["handlers"] = ["console"]
LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["django.request"]["level"] = "DEBUG"

# Celery 开发环境立即执行任务（可选），实际仍走 RabbitMQ 以便验证链路
# CELERY_TASK_ALWAYS_EAGER = True
