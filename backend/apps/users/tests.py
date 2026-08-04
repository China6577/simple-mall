"""用户模块测试。"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class AuthAPITests(TestCase):
    """认证相关接口测试。"""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.refresh_url = reverse("token-refresh")
        self.me_url = reverse("user-me")

    def test_register_success(self):
        """正常注册返回 201 和 Token。"""
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "alice@example.com")
        self.assertEqual(User.objects.count(), 1)

    def test_register_password_mismatch(self):
        """两次密码不一致返回 400。"""
        payload = {
            "username": "bob",
            "email": "bob@example.com",
            "password": "StrongPass123",
            "confirm_password": "DifferentPass123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        """重复邮箱返回 400。"""
        User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        payload = {
            "username": "alice2",
            "email": "alice@example.com",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }
        response = self.client.post(self.register_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """邮箱 + 密码登录成功。"""
        User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        response = self.client.post(self.login_url, {
            "email": "alice@example.com",
            "password": "StrongPass123",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertEqual(response.data["user"]["email"], "alice@example.com")

    def test_login_wrong_password(self):
        """密码错误返回 400，不泄露账号是否存在。"""
        User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        response = self.client.post(self.login_url, {
            "email": "alice@example.com",
            "password": "wrongpassword",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_case_insensitive_email(self):
        """邮箱大小写不敏感。"""
        User.objects.create_user(username="alice", email="Alice@Example.com", password="StrongPass123")
        response = self.client.post(self.login_url, {
            "email": "alice@example.com",
            "password": "StrongPass123",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_token(self):
        """Refresh Token 可以换取新的 Access Token。"""
        user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response = self.client.post(self.refresh_url, {"refresh": str(refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_get_me_requires_auth(self):
        """未认证访问 /me 返回 401。"""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me_success(self):
        """认证后获取当前用户信息。"""
        user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        self.client.force_authenticate(user=user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "alice")

    def test_logout_blacklists_refresh_token(self):
        """退出后 Refresh Token 无法再次使用。"""
        user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        self.client.force_authenticate(user=user)
        response = self.client.post(self.logout_url, {"refresh": str(refresh)}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 再次刷新应失败
        response2 = self.client.post(self.refresh_url, {"refresh": str(refresh)}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordTests(TestCase):
    """修改密码测试。"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("change-password")
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="OldPass123")
        self.client.force_authenticate(user=self.user)

    def test_change_password_success(self):
        response = self.client.post(self.url, {
            "old_password": "OldPass123",
            "new_password": "NewPass123456",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass123456"))

    def test_change_password_wrong_old(self):
        response = self.client.post(self.url, {
            "old_password": "wrong",
            "new_password": "NewPass123456",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AddressAPITests(TestCase):
    """收货地址接口测试。"""

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("address-list")
        self.user = User.objects.create_user(username="alice", email="alice@example.com", password="StrongPass123")
        self.client.force_authenticate(user=self.user)

    def test_create_address(self):
        from apps.users.models import Address

        payload = {
            "receiver": "张三",
            "phone": "13800138000",
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "detail": "科技园 123 号",
        }
        response = self.client.post(self.url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Address.objects.filter(user=self.user).count(), 1)

    def test_address_default_unique(self):
        """设置新的默认地址后，旧地址自动取消默认。"""
        from apps.users.models import Address

        addr1 = Address.objects.create(
            user=self.user, receiver="张三", phone="13800138000",
            province="广东省", city="深圳市", district="南山区", detail="A", is_default=True
        )
        self.client.post(self.url, {
            "receiver": "李四",
            "phone": "13800138001",
            "province": "广东省", "city": "深圳市", "district": "福田区", "detail": "B",
            "is_default": True,
        }, format="json")
        addr1.refresh_from_db()
        self.assertFalse(addr1.is_default)

    def test_cannot_access_others_address(self):
        """不能查看或修改其他用户的地址。"""
        from apps.users.models import Address

        other = User.objects.create_user(username="bob", email="bob@example.com", password="StrongPass123")
        addr = Address.objects.create(
            user=other, receiver="Bob", phone="13800138000",
            province="北京", city="北京市", district="朝阳区", detail="X"
        )
        response = self.client.get(reverse("address-detail", kwargs={"pk": addr.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
