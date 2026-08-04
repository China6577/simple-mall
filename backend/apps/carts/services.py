"""购物车辅助服务：摘要计算与 Redis 缓存。"""

from django.core.cache import cache

CART_SUMMARY_CACHE_KEY = "cart:summary:{user_id}"
CART_SUMMARY_TIMEOUT = 300  # 5 分钟


def calculate_cart_summary(items):
    """根据购物车条目列表计算摘要。"""
    total_count = sum(item.quantity for item in items)
    selected_count = sum(item.quantity for item in items if item.selected)
    total_amount = sum(
        item.sku.price * item.quantity
        for item in items
        if item.selected
    )
    return {
        "total_count": total_count,
        "selected_count": selected_count,
        "total_amount": total_amount,
    }


def get_cart_summary_cache(user_id):
    """从 Redis 读取购物车摘要。"""
    return cache.get(CART_SUMMARY_CACHE_KEY.format(user_id=user_id))


def set_cart_summary_cache(user_id, summary, timeout=CART_SUMMARY_TIMEOUT):
    """把购物车摘要写入 Redis。"""
    cache.set(CART_SUMMARY_CACHE_KEY.format(user_id=user_id), summary, timeout=timeout)


def delete_cart_summary_cache(user_id):
    """购物车变更时删除摘要缓存。"""
    cache.delete(CART_SUMMARY_CACHE_KEY.format(user_id=user_id))
