"""
创建默认管理员账号。

Docker Compose 启动后可通过本脚本自动创建管理员，避免手动执行 createsuperuser。
"""

import os
import sys

import django

# 当通过 `python scripts/init_admin.py` 运行时，确保项目根目录在 Python 路径中
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
django.setup()

from apps.users.models import User


def create_admin():
    username = os.getenv("DJANGO_ADMIN_USERNAME", "admin")
    email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@mall.local")
    password = os.getenv("DJANGO_ADMIN_PASSWORD", "123456")

    if User.objects.filter(username=username).exists():
        print(f"Admin user '{username}' already exists.")
        return

    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password,
        role=User.Role.ADMIN,
    )
    print(f"Admin user '{user.username}' created successfully.")


if __name__ == "__main__":
    create_admin()
