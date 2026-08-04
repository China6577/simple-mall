"""统一 JSON 响应渲染器。"""

from rest_framework.renderers import JSONRenderer


class StandardJSONRenderer(JSONRenderer):
    """
    将 DRF 的默认响应包装为统一格式：

        {"code": 0, "message": "success", "data": ...}

    如果视图已经返回了包含 code/message/data 的字典，则不再包装。
    """

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response = renderer_context.get("response") if renderer_context else None

        # 异常响应不在这里包装，由全局异常处理器负责
        if response is not None and not (200 <= response.status_code < 300):
            return super().render(data, accepted_media_type, renderer_context)

        if isinstance(data, dict) and "code" in data and "message" in data and "data" in data:
            return super().render(data, accepted_media_type, renderer_context)

        wrapped = {"code": 0, "message": "success", "data": data if data is not None else {}}
        return super().render(wrapped, accepted_media_type, renderer_context)
