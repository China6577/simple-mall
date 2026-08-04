"""通用校验函数。"""

import re

from django.core.exceptions import ValidationError


def validate_phone(value):
    """校验中国大陆手机号。"""
    if not re.match(r"^1[3-9]\d{9}$", value):
        raise ValidationError("请输入有效的手机号")


def validate_email(value):
    """简单但严格的邮箱格式校验。"""
    if not re.match(r"^[\w.-]+@[\w.-]+\.\w+$", value):
        raise ValidationError("请输入有效的邮箱地址")
