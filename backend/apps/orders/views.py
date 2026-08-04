"""订单模块视图。"""

import uuid

from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import BusinessException, ConflictException, NotFoundException, ValidationException
from apps.common.pagination import StandardPagination
from apps.common.permissions import IsOperator

from .models import Order
from .serializers import OrderCreateSerializer, OrderDetailSerializer, OrderListSerializer
from .services import cancel_order, confirm_receive_order, create_order, ship_order


ORDER_LOCK_KEY = "lock:order:create:{user_id}:{idempotency_key}"
LOCK_TIMEOUT = 30


def _acquire_create_lock(user_id, idempotency_key):
    """获取订单创建锁，防止重复提交。"""
    key = ORDER_LOCK_KEY.format(user_id=user_id, idempotency_key=idempotency_key)
    value = str(uuid.uuid4())
    if cache.add(key, value, timeout=LOCK_TIMEOUT):
        return value
    return None


def _release_create_lock(user_id, idempotency_key, value):
    """释放订单创建锁。"""
    key = ORDER_LOCK_KEY.format(user_id=user_id, idempotency_key=idempotency_key)
    if cache.get(key) == value:
        cache.delete(key)


class OrderListCreateView(generics.ListCreateAPIView):
    """订单列表与创建。"""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardPagination

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_deleted=False).prefetch_related("items")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return OrderCreateSerializer
        return OrderListSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        cart_item_ids = data["cart_item_ids"]
        address_id = data["address_id"]
        remark = data.get("remark", "")
        idempotency_key = data.get("idempotency_key") or str(uuid.uuid4())
        coupon_ids = data.get("coupon_ids") or []

        lock_value = _acquire_create_lock(request.user.id, idempotency_key)
        if not lock_value:
            raise ConflictException("订单正在处理中，请勿重复提交")

        try:
            order = create_order(
                user=request.user,
                cart_item_ids=cart_item_ids,
                address_id=address_id,
                remark=remark,
                idempotency_key=idempotency_key,
                coupon_ids=coupon_ids,
            )
        finally:
            _release_create_lock(request.user.id, idempotency_key, lock_value)

        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )


class OrderDetailView(generics.RetrieveAPIView):
    """订单详情。"""

    permission_classes = [IsAuthenticated]
    serializer_class = OrderDetailSerializer
    lookup_field = "order_no"

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user, is_deleted=False).prefetch_related("items")


class OrderCancelView(APIView):
    """用户取消订单。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            raise NotFoundException("订单不存在")

        cancel_order(order, request.user)
        return Response({"message": "订单已取消"})


class OrderPayView(APIView):
    """
    模拟支付。

    前端调用此接口模拟用户完成支付，后端会生成支付流水并调用支付回调服务
    完成订单状态变更和库存扣减。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        from apps.payments.services import pay_order

        try:
            order = Order.objects.get(order_no=order_no, user=request.user)
        except Order.DoesNotExist:
            raise NotFoundException("订单不存在")

        payment_no = pay_order(order, request.user)
        return Response({"message": "支付成功", "payment_no": payment_no})


class OrderShipView(APIView):
    """运营/管理员发货。"""

    permission_classes = [IsAuthenticated, IsOperator]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no)
        except Order.DoesNotExist:
            raise NotFoundException("订单不存在")

        ship_order(order, request.user)
        return Response({"message": "发货成功"})


class OrderConfirmView(APIView):
    """用户确认收货。"""

    permission_classes = [IsAuthenticated]

    def post(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user, is_deleted=False)
        except Order.DoesNotExist:
            raise NotFoundException("订单不存在")

        confirm_receive_order(order, request.user)
        return Response({"message": "确认收货成功"})


class OrderDeleteView(APIView):
    """用户删除订单（软删除）。"""

    permission_classes = [IsAuthenticated]

    def delete(self, request, order_no):
        try:
            order = Order.objects.get(order_no=order_no, user=request.user, is_deleted=False)
        except Order.DoesNotExist:
            raise NotFoundException("订单不存在")

        # 只允许删除已完成或已取消的订单
        if order.status not in (Order.Status.COMPLETED, Order.Status.CANCELLED):
            raise ValidationException("只能删除已完成或已取消的订单")

        order.is_deleted = True
        order.save(update_fields=["is_deleted"])
        return Response({"message": "订单已删除"})
