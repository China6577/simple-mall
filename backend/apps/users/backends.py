"""自定义认证后端。

由于用户模型以邮箱作为 USERNAME_FIELD，普通用户通过邮箱登录前台；
但 Django 管理后台仍希望超级管理员/运营人员使用用户名登录。
这里提供两个后端，分别处理这两种场景。
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    邮箱认证后端。

    供前台普通用户使用邮箱 + 密码登录。
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        # SimpleJWT 使用 email 字段调用 authenticate，Django admin 使用 username
        email = kwargs.get("email") or username
        if not email or not password:
            return None
        # 只处理邮箱形式的凭证
        if "@" not in email:
            return None
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None


class UsernameForStaffBackend(ModelBackend):
    """
    用户名认证后端（仅用于员工/管理员）。

    供 Django 管理后台使用用户名 + 密码登录。
    只放行 is_staff 或 is_superuser 的用户，避免普通用户通过用户名登录后台。

    由于 username 允许重复，当存在多个同名用户时，优先匹配具有后台权限的用户。
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        username = kwargs.get("username") or username
        if not username or not password:
            return None
        # 只处理非邮箱形式的凭证
        if "@" in username:
            return None
        users = User.objects.filter(username=username)
        if not users.exists():
            return None

        # 优先选择有后台权限的用户；若都不具备，则拒绝登录
        staff_users = users.filter(is_staff=True) | users.filter(is_superuser=True)
        candidates = staff_users.distinct() if staff_users.exists() else users.none()

        for user in candidates:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None
