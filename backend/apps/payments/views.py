"""支付模块视图。"""

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.exceptions import BusinessException, NotFoundException, ValidationException

from .models import PaymentRecord
from .services import process_payment_callback


class PaymentCallbackView(APIView):
    """
    模拟支付回调接口。

    接收 { order_no, payment_no, amount }，幂等地处理支付结果。
    用于教学演示和测试；生产环境应替换为真实支付网关回调。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_no = request.data.get("order_no")
        payment_no = request.data.get("payment_no")
        amount = request.data.get("amount")

        if not order_no or not payment_no or amount is None:
            raise ValidationException("order_no、payment_no、amount 均不能为空")

        try:
            record = process_payment_callback(
                order_no=order_no,
                payment_no=payment_no,
                amount=amount,
                callback_data=request.data,
            )
        except PaymentRecord.DoesNotExist:
            raise NotFoundException("支付记录不存在")

        return Response({
            "message": "回调处理成功",
            "payment_no": record.payment_no,
            "status": record.status,
        })
