"""
Celery 应用配置。

RabbitMQ 作为 Broker，Redis 作为结果后端。
Django 启动时会通过 config/__init__.py 自动加载本文件。
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

app = Celery("mall")

# 从 Django 配置中读取 CELERY_* 开头的配置
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有 App 中的 tasks.py
app.autodiscover_tasks()
