"""通用中间件。"""

import logging
import time

from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("django.request")


class RequestLogMiddleware(MiddlewareMixin):
    """
    请求日志中间件。

    记录每个请求的 Method、Path、Status Code 和耗时。
    注意：不记录请求体，避免泄露密码或 Token。
    """

    def process_request(self, request):
        request._request_start_time = time.time()
        return None

    def process_response(self, request, response):
        duration = time.time() - getattr(request, "_request_start_time", time.time())
        logger.info(
            "method=%s path=%s status=%s duration=%.3fs",
            request.method,
            request.path,
            response.status_code,
            duration,
        )
        return response
