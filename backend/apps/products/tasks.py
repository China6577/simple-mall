"""商品模块 Celery 异步任务。"""

from celery import shared_task
from django.conf import settings
from django.core.cache import cache

from apps.inventory.models import Stock
from apps.orders.models import OrderItem

from .models import SKU, Category, SPU


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def check_low_stock_and_alert(self, threshold=10):
    """
    检查低库存 SKU 并输出预警。

    默认阈值 10，实际项目中可接入企业微信/钉钉/邮件通知。
    结果缓存 1 小时，避免重复告警。
    """
    cache_key = "tasks:low_stock_alert:last_run"
    if cache.get(cache_key):
        return {"status": "skipped", "reason": "already_run_recently"}

    low_stock_items = []
    for stock in Stock.objects.select_related("sku__spu").iterator():
        if stock.available <= threshold:
            low_stock_items.append({
                "sku_code": stock.sku.sku_code,
                "spu_name": stock.sku.spu.name,
                "available": stock.available,
                "quantity": stock.quantity,
                "locked": stock.locked_quantity,
            })

    # 开发阶段先打印到日志/控制台；后续可接入消息通知
    for item in low_stock_items:
        print(
            f"[库存预警] SKU: {item['sku_code']} 商品: {item['spu_name']} "
            f"可售: {item['available']} 总库存: {item['quantity']} 锁定: {item['locked']}"
        )

    cache.set(cache_key, True, timeout=3600)
    return {"status": "ok", "alert_count": len(low_stock_items), "items": low_stock_items}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def refresh_product_sales_stats(self):
    """
    刷新商品销量与分类销量统计。

    统计已支付订单的订单项数量，更新 SKU.sales 与 SPU/Category 缓存。
    """
    # 按 SKU 聚合销量
    sku_sales = {}
    spu_sales = {}
    category_sales = {}

    for item in OrderItem.objects.filter(
        order__status__in=["paid", "shipped", "completed"]
    ).select_related("sku__spu__category"):
        sku_id = item.sku_id
        spu_id = item.sku.spu_id
        category_id = item.sku.spu.category_id

        sku_sales[sku_id] = sku_sales.get(sku_id, 0) + item.quantity
        spu_sales[spu_id] = spu_sales.get(spu_id, 0) + item.quantity
        category_sales[category_id] = category_sales.get(category_id, 0) + item.quantity

    # 批量更新 SKU 销量
    skus_to_update = []
    for sku in SKU.objects.filter(id__in=sku_sales.keys()):
        sku.sales = sku_sales.get(sku.id, 0)
        skus_to_update.append(sku)
    if skus_to_update:
        SKU.objects.bulk_update(skus_to_update, ["sales"])

    # 将 SPU/Category 销量写入缓存，供首页排行榜使用
    cache.set("stats:spu_sales", spu_sales, timeout=3600)
    cache.set("stats:category_sales", category_sales, timeout=3600)

    return {
        "status": "ok",
        "sku_count": len(sku_sales),
        "spu_count": len(spu_sales),
        "category_count": len(category_sales),
    }
