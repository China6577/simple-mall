"""用户相关表单。"""

from django.contrib.auth.forms import AuthenticationForm


class StaffLoginForm(AuthenticationForm):
    """
    员工/管理员登录表单。

    由于用户模型以邮箱作为 USERNAME_FIELD，Django 管理后台登录页默认显示
    "邮箱地址" 标签。这里将标签改为 "用户名"，以便管理员使用用户名登录后台。
    """

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        self.fields["username"].label = "用户名"
