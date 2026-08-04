"""购物车模块视图。

API 列表：
- GET    /carts/          查询当前用户购物车
- POST   /carts/items/    添加商品
- PUT    /carts/items/{id}/  修改数量/选中状态
- DELETE /carts/items/{id}/  删除商品
- POST   /carts/select/   批量选中/取消
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import NotFoundException

from .models import CartItem
from .serializers import (
    CartItemCreateSerializer,
    CartItemSerializer,
    CartItemUpdateSerializer,
)
from .services import (
    calculate_cart_summary,
    delete_cart_summary_cache,
    get_cart_summary_cache,
    set_cart_summary_cache,
)


class CartListView(APIView):
    """查询当前用户购物车列表及摘要。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related(
            "sku__spu", "sku__stock_record"
        )
        serializer = CartItemSerializer(items, many=True, context={"request": request})

        summary = get_cart_summary_cache(request.user.id)
        if summary is None:
            summary = calculate_cart_summary(items)
            set_cart_summary_cache(request.user.id, summary)

        return Response({"items": serializer.data, "summary": summary})


class CartItemCreateView(APIView):
    """添加商品到购物车。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CartItemCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        item = serializer.save()
        delete_cart_summary_cache(request.user.id)
        return Response(
            CartItemSerializer(item, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CartItemDetailView(APIView):
    """修改/删除购物车条目。"""

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return CartItem.objects.get(pk=pk, user=user)
        except CartItem.DoesNotExist:
            raise NotFoundException("购物车商品不存在")

    def put(self, request, pk):
        item = self.get_object(pk, request.user)
        serializer = CartItemUpdateSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        delete_cart_summary_cache(request.user.id)
        return Response(CartItemSerializer(item, context={"request": request}).data)

    def delete(self, request, pk):
        item = self.get_object(pk, request.user)
        item.delete()
        delete_cart_summary_cache(request.user.id)
        return Response({"message": "删除成功"}, status=status.HTTP_200_OK)


class CartSelectView(APIView):
    """批量选中/取消选中购物车条目。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        item_ids = request.data.get("item_ids", [])
        selected = request.data.get("selected", True)

        if not isinstance(item_ids, list):
            return Response(
                {"code": 4000, "message": "item_ids 必须是数组", "data": {}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        CartItem.objects.filter(user=request.user, id__in=item_ids).update(selected=selected)
        delete_cart_summary_cache(request.user.id)
        return Response({"message": "操作成功"})
