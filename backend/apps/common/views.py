"""通用视图：健康检查等。"""

from django.db import connection
from django.http import JsonResponse


def health_check(request):
    """服务健康检查，返回数据库与 Redis 状态。"""
    status = {"status": "ok", "checks": {}}

    # 数据库检查
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        status["checks"]["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        status["checks"]["database"] = f"error: {exc}"
        status["status"] = "error"

    # Redis 检查
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", timeout=5)
        value = cache.get("health_check")
        status["checks"]["redis"] = "ok" if value == "ok" else f"unexpected: {value}"
    except Exception as exc:  # noqa: BLE001
        status["checks"]["redis"] = f"error: {exc}"
        status["status"] = "error"

    code = 200 if status["status"] == "ok" else 503
    return JsonResponse(status, status=code)
