"""用户模块序列化器。"""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from apps.common.validators import validate_phone

from .models import Address, User


class UserSerializer(serializers.ModelSerializer):
    """
    用户信息序列化器。

    用于返回当前登录用户详情；敏感字段（如密码、角色以外的内部字段）不暴露。
    """

    avatar_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "avatar", "avatar_url", "role", "date_joined"]
        read_only_fields = ["id", "email", "role", "date_joined"]

    def get_avatar_url(self, obj):
        """返回头像完整 URL。"""
        if not obj.avatar:
            return ""
        request = self.context.get("request")
        url = obj.avatar.url
        if request:
            return request.build_absolute_uri(url)
        return url


class UserUpdateSerializer(serializers.ModelSerializer):
    """用户更新个人资料。"""

    phone = serializers.CharField(validators=[validate_phone], required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ["username", "phone", "avatar"]


class RegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器。

    注册时校验邮箱唯一性、两次密码是否一致；用户名允许重复，不做唯一性校验。
    """

    password = serializers.CharField(write_only=True, min_length=8, label="密码")
    confirm_password = serializers.CharField(write_only=True, label="确认密码")

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password", "phone"]
        # 关闭 DRF 自动添加的邮箱唯一性校验器，使用自定义 validate_email 提示。
        extra_kwargs = {
            "email": {"validators": []},
        }

    def validate_email(self, value):
        """邮箱转小写并去重校验。"""
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return email

    def validate_password(self, value):
        """复用 Django 内置密码强度校验。"""
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            phone=validated_data.get("phone", ""),
        )
        return user

    def to_representation(self, instance):
        """注册成功后直接返回用户信息和 Token。"""
        refresh = RefreshToken.for_user(instance)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(instance).data,
        }


class EmailLoginSerializer(serializers.Serializer):
    """
    邮箱登录序列化器。

    因为项目要求只用邮箱登录，而 Django/SimpleJWT 默认使用 username，
    所以这里手动根据邮箱查询用户、校验密码，再生成 JWT Token 对。
    """

    email = serializers.EmailField(label="邮箱")
    password = serializers.CharField(write_only=True, label="密码")

    def validate(self, attrs):
        email = attrs["email"].lower().strip()
        password = attrs["password"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("邮箱或密码错误")

        if not user.check_password(password):
            raise serializers.ValidationError("邮箱或密码错误")

        if not user.is_active:
            raise serializers.ValidationError("账号已被禁用，请联系管理员")

        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }


class ChangePasswordSerializer(serializers.Serializer):
    """修改密码序列化器。"""

    old_password = serializers.CharField(write_only=True, label="原密码")
    new_password = serializers.CharField(write_only=True, min_length=8, label="新密码")

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码错误")
        return value

    def validate_new_password(self, value):
        validate_password(value)
        return value

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save(update_fields=["password"])
        return user


class AddressSerializer(serializers.ModelSerializer):
    """收货地址序列化器。"""

    class Meta:
        model = Address
        exclude = ["user"]
        read_only_fields = ["created_at", "updated_at"]

    def _ensure_single_default(self, user, exclude_id=None):
        """设置默认地址时，把该用户其他地址设为非默认。"""
        queryset = Address.objects.filter(user=user)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        queryset.update(is_default=False)

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        if validated_data.get("is_default"):
            self._ensure_single_default(validated_data["user"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if validated_data.get("is_default"):
            self._ensure_single_default(instance.user, exclude_id=instance.id)
        return super().update(instance, validated_data)
