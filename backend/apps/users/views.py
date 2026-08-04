"""用户模块视图。"""

from rest_framework import generics, status, throttling
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.views import TokenRefreshView as BaseTokenRefreshView

from .models import Address
from .serializers import (
    AddressSerializer,
    ChangePasswordSerializer,
    EmailLoginSerializer,
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
)


class AnonRateThrottle(throttling.AnonRateThrottle):
    """匿名用户严格限流，用于登录注册等接口。"""

    rate = "10/minute"


class RegisterView(APIView):
    """
    用户注册。

    接收 username、email、password、confirm_password、phone，
    校验通过后创建用户并返回 JWT Token 对。
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # to_representation 中已包含 access/refresh/user
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    用户登录（邮箱 + 密码）。

    校验成功后返回 Access Token、Refresh Token 和用户信息。
    登录失败次数由限流控制，避免暴力破解。
    """

    permission_classes = []
    authentication_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


class TokenRefreshView(BaseTokenRefreshView):
    """
    刷新 Access Token。

    直接使用 SimpleJWT 的视图；由于启用了 ROTATE_REFRESH_TOKENS，
    刷新时会同时返回新的 Refresh Token，旧的会被加入黑名单。
    """

    pass


class LogoutView(APIView):
    """
    退出登录。

    把传入的 Refresh Token 加入黑名单，使其无法再刷新 Access Token。
    即使 Token 解析失败也返回成功，保证客户端可以安全清理本地状态。
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                # Token 已过期或已失效，本地清理即可
                pass
        return Response({"message": "退出成功"})


class UserMeView(APIView):
    """当前登录用户信息。"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ChangePasswordView(APIView):
    """修改当前用户密码。"""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "密码修改成功"})


class AddressListCreateView(generics.ListCreateAPIView):
    """收货地址列表与新增。"""

    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只返回当前用户的地址。"""
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """自动把地址关联到当前用户。"""
        serializer.save(user=self.request.user)


class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    """收货地址详情、更新、删除。"""

    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """防止越权访问其他用户的地址（IDOR）。"""
        return Address.objects.filter(user=self.request.user)
