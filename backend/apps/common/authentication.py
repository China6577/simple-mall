"""JWT 认证入口。"""

from rest_framework_simplejwt.authentication import JWTAuthentication as BaseJWTAuthentication


class JWTAuthentication(BaseJWTAuthentication):
    """
    项目统一的 JWT 认证类。

    继承 SimpleJWT 的默认实现，未来可在这里扩展：
    - Access Token 黑名单校验
    - 自定义 User 查询逻辑
    """

    www_authenticate_realm = "api"
