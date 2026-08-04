"""邮件发送工具。

开发/测试环境使用控制台或内存后端，不依赖真实 SMTP。
生产环境可通过环境变量切换为 SMTP 后端。
"""

from django.conf import settings
from django.core.mail import send_mail


def send_templated_email(subject, message, recipient_list, html_message=None):
    """
    发送邮件。

    参数：
        subject: 邮件主题
        message: 纯文本内容
        recipient_list: 收件人邮箱列表
        html_message: HTML 内容（可选）
    """
    if not recipient_list:
        return

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=recipient_list,
        html_message=html_message,
        fail_silently=True,
    )
