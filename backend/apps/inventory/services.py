"""库存业务服务。

提供库存锁定、释放、扣减的封装，所有操作均在事务中完成，
并使用 select_for_update() 行锁防止并发超卖。
"""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.common.exceptions import BusinessException, ValidationException

from .models import Stock, StockLog


def _get_stock_for_update(sku_id):
    """获取并锁定库存记录。"""
    try:
        return Stock.objects.select_for_update().get(sku_id=sku_id)
    except Stock.DoesNotExist:
        raise ValidationException("库存记录不存在")


def _create_stock_log(stock, change_quantity, locked_change, reason, operator=None):
    """创建库存变更日志。"""
    return StockLog.objects.create(
        stock=stock,
        change_quantity=change_quantity,
        locked_change=locked_change,
        available_after=stock.available,
        reason=reason,
        operator=operator,
    )


def lock_stock(sku_id, quantity, reason, operator=None):
    """
    锁定库存。

    创建订单时调用，增加 locked_quantity，减少可售库存。
    """
    if quantity <= 0:
        raise ValidationException("锁定数量必须大于 0")

    with transaction.atomic():
        stock = _get_stock_for_update(sku_id)
        if stock.available < quantity:
            raise BusinessException("库存不足")
        stock.locked_quantity += quantity
        stock.version += 1
        stock.save(update_fields=["locked_quantity", "version", "updated_at"])
        _create_stock_log(stock, 0, quantity, reason, operator)
        return stock


def release_stock(sku_id, quantity, reason, operator=None):
    """
    释放锁定库存。

    取消订单或超时未支付时调用，减少 locked_quantity，恢复可售库存。
    """
    if quantity <= 0:
        raise ValidationException("释放数量必须大于 0")

    with transaction.atomic():
        stock = _get_stock_for_update(sku_id)
        if stock.locked_quantity < quantity:
            raise BusinessException("锁定库存不足")
        stock.locked_quantity -= quantity
        stock.version += 1
        stock.save(update_fields=["locked_quantity", "version", "updated_at"])
        _create_stock_log(stock, 0, -quantity, reason, operator)
        return stock


def deduct_stock(sku_id, quantity, reason, operator=None):
    """
    扣减实际库存。

    支付成功后调用，同时减少 quantity 和 locked_quantity。
    可售库存保持不变（因为锁定阶段已减少）。
    """
    if quantity <= 0:
        raise ValidationException("扣减数量必须大于 0")

    with transaction.atomic():
        stock = _get_stock_for_update(sku_id)
        if stock.locked_quantity < quantity:
            raise BusinessException("锁定库存不足")
        if stock.quantity < quantity:
            raise BusinessException("实际库存不足")
        stock.quantity -= quantity
        stock.locked_quantity -= quantity
        stock.version += 1
        stock.save(update_fields=["quantity", "locked_quantity", "version", "updated_at"])
        _create_stock_log(stock, -quantity, -quantity, reason, operator)
        return stock
