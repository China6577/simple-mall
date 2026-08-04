"""项目通用权限类。"""

from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """仅管理员可访问。"""

    message = "需要管理员权限"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsOperator(permissions.BasePermission):
    """管理员或运营人员可访问。"""

    message = "需要运营权限"

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ("admin", "operator")


class IsOwner(permissions.BasePermission):
    """对象所有者才可访问，用于单对象详情/更新/删除。"""

    message = "只能操作自己的数据"

    def has_object_permission(self, request, view, obj):
        # 优先使用 user 字段；如果没有，则使用 owner 字段
        owner = getattr(obj, "user", None) or getattr(obj, "owner", None)
        return owner == request.user
