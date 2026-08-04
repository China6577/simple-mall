"""
业务异常与全局异常处理。

统一将 DRF 和 Django 异常转换为标准响应格式：
{
    "code": <非零错误码>,
    "message": "错误描述",
    "data": {}
}
"""

import logging

from django_ratelimit.exceptions import Ratelimited
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("django.request")


class BusinessException(APIException):
    """通用业务异常，可被视图主动抛出。"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "business_error"
    default_detail = "业务处理失败"

    def __init__(self, detail=None, code=None, status_code=None):
        if status_code is not None:
            self.status_code = status_code
        super().__init__(detail=detail, code=code)


class ConflictException(BusinessException):
    """资源冲突，例如重复提交。"""

    status_code = status.HTTP_409_CONFLICT
    default_code = "conflict"
    default_detail = "资源冲突"


class NotFoundException(BusinessException):
    """资源不存在。"""

    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"
    default_detail = "资源不存在"


class ValidationException(BusinessException):
    """参数校验失败。"""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "validation_error"
    default_detail = "参数错误"


def standard_exception_handler(exc, context):
    """
    全局异常处理器。

    先调用 DRF 默认处理器拿到 Response，再包装成统一格式。
    """
    # 限流异常由 django-ratelimit 抛出，需要单独处理
    if isinstance(exc, Ratelimited):
        return Response(
            {"code": 4290, "message": "请求过于频繁，请稍后再试", "data": {}},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    response = exception_handler(exc, context)

    if response is None:
        # 未处理的异常记录详细堆栈，便于排查
        logger.exception("unhandled exception: %s", exc)
        return Response(
            {"code": 5000, "message": "服务器内部错误", "data": {}},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_code = getattr(exc, "code", None) or "error"
    message = _extract_message(response.data)

    standardized = {
        "code": _status_to_code(response.status_code),
        "message": message,
        "data": {},
    }
    return Response(standardized, status=response.status_code)


def _extract_message(data):
    """从 DRF 异常响应数据中提取可读的字符串错误信息。"""
    if not isinstance(data, dict):
        return str(data) if data else "请求失败"

    if "detail" in data:
        return str(data["detail"])

    # 非字段错误（如序列化器 validate() 抛出的错误）
    if "non_field_errors" in data:
        errors = data["non_field_errors"]
        if isinstance(errors, list):
            return "；".join(str(e) for e in errors)
        return str(errors)

    # 字段级校验错误，只返回错误文本，不拼字段名，便于前端直接展示
    if data:
        parts = []
        for errors in data.values():
            if isinstance(errors, list):
                parts.append(", ".join(str(e) for e in errors))
            else:
                parts.append(str(errors))
        return "；".join(parts)

    return "请求失败"


def _status_to_code(status_code):
    """将 HTTP 状态码映射为业务错误码，便于前端统一判断。"""
    mapping = {
        400: 4000,
        401: 4010,
        403: 4030,
        404: 4040,
        409: 4090,
        429: 4290,
        500: 5000,
    }
    return mapping.get(status_code, 5000)
