# 阶段三：用户和认证模块

## 1. 本阶段目标

实现用户注册、登录、JWT Token 颁发与刷新、退出登录、当前用户信息、修改密码、收货地址管理等核心认证接口，并配套前端登录/注册页面与路由守卫。

## 2. 设计思路

- **用户模型继承 `AbstractUser`**：复用 Django 内置密码哈希、权限组、激活状态，只扩展 `phone`、`avatar`、`role` 字段。
- **登录只用邮箱 + 密码**：自定义 `EmailLoginSerializer`，先按邮箱查询用户，再校验密码，避免改造 Django 认证后端。
- **JWT 双 Token**：Access Token 15 分钟、Refresh Token 7 天；开启 `ROTATE_REFRESH_TOKENS` 和黑名单，退出时让 Refresh Token 失效。
- **权限分层**：`IsAuthenticated` 用于普通用户接口；`IsAdmin` / `IsOperator` 放在 `common.permissions` 中供后续阶段使用。
- **收货地址防越权**：地址详情/列表只返回当前用户数据，防止 IDOR。
- **限流防暴力破解**：注册/登录视图使用 DRF `AnonRateThrottle`，限制 10 次/分钟。
- **测试不依赖 MySQL/Redis**：新增 `config.settings.test`，使用 SQLite 内存数据库 + LocMemCache。

## 3. 新增或修改的文件

### 后端

- `apps/users/models.py`：新增 `Address` 模型。
- `apps/users/serializers.py`：新增注册、登录、用户信息、修改密码、地址序列化器。
- `apps/users/views.py`：新增注册、登录、Token 刷新、退出、当前用户、修改密码、地址 CRUD 视图。
- `apps/users/urls.py`：挂载认证与用户相关路由。
- `apps/users/admin.py`：增加 `AddressInline` 和 `AddressAdmin`。
- `apps/users/tests.py`：15 个自动化测试用例。
- `apps/common/permissions.py`：新增 `IsAdmin`、`IsOperator`、`IsOwner`。
- `apps/common/exceptions.py`：增加 `Ratelimited` 异常处理。
- `config/settings/test.py`：新增测试环境配置（SQLite + LocMemCache）。
- `config/settings/base.py`：加长默认 `SECRET_KEY` 至 32 字节以上。
- `apps/users/migrations/0002_address.py`：自动生成的地址表迁移。

### 前端

- `src/api/auth.js`：`logout` 方法接收 refresh token 参数。
- `src/components/AppHeader.vue`：退出时调用后端 logout 接口并清空本地状态。
- `src/views/auth/LoginView.vue`：已存在并兼容阶段三接口。
- `src/views/auth/RegisterView.vue`：已存在并兼容阶段三接口。

## 4. 核心代码逐段解释

### 4.1 自定义邮箱登录序列化器

```python
class EmailLoginSerializer(serializers.Serializer):
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
```

**解释**：Django 和 SimpleJWT 默认用 `username` 登录。这里直接按邮箱查用户，再调用 `check_password` 校验哈希密码。验证通过后调用 `RefreshToken.for_user(user)` 生成 Token 对，并附带序列化后的用户信息。

### 4.2 注册序列化器

```python
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirm_password", "phone"]
        extra_kwargs = {
            "email": {"validators": []},
            "username": {"validators": []},
        }

    def validate_email(self, value):
        email = value.lower().strip()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("该邮箱已被注册")
        return email

    def validate_password(self, value):
        validate_password(value)
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        return attrs
```

**解释**：`extra_kwargs` 关闭 DRF 自动添加的唯一性校验器，避免与自定义校验冲突。`validate_password` 复用 Django 内置密码强度校验（最短 8 位、常见密码检查等）。

### 4.3 退出登录（Refresh Token 黑名单）

```python
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except TokenError:
                pass
        return Response({"message": "退出成功"})
```

**解释**：用户退出时把 Refresh Token 加入黑名单，后续无法再用它换取新的 Access Token。即使 Token 已过期也返回成功，确保客户端能完成本地清理。

### 4.4 地址防越权

```python
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
```

**解释**：通过限制 queryset 只包含当前用户的地址，DRF 的 `get_object()` 在找不到记录时自动返回 404，防止用户 A 用 ID 访问用户 B 的地址。

### 4.5 限流

```python
class AnonRateThrottle(throttling.AnonRateThrottle):
    rate = "10/minute"

class RegisterView(APIView):
    throttle_classes = [AnonRateThrottle]
```

**解释**：匿名用户注册/登录每分钟最多 10 次，降低暴力破解和垃圾注册风险。DRF throttle 默认使用 Django cache，开发/生产配置为 Redis，测试环境切换为 LocMemCache。

### 4.6 前端 Axios Token 刷新

```js
request.interceptors.response.use(
  (response) => { ... },
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          refreshSubscribers.push((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }
      originalRequest._retry = true
      isRefreshing = true
      try {
        const newToken = await refreshAccessToken()
        refreshSubscribers.forEach((callback) => callback(newToken))
        refreshSubscribers = []
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return request(originalRequest)
      } catch (refreshError) {
        userStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    ...
  }
)
```

**解释**：
- 请求拦截器自动附加 Access Token。
- 收到 401 时，用 Refresh Token 换取新的 Access Token。
- 多个并发请求同时 401 时，只触发一次刷新，其他请求排队等待新 Token。
- 刷新失败则清空登录态并跳转登录页。

## 5. 安装和运行命令

### 启动 Docker 开发环境

```bash
cd C:\Users\36413\Desktop\vibe-codeing-project
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

docker-compose up -d --build
```

### 本地启动后端

```bash
cd backend
pip install -r requirements/dev.txt
python manage.py migrate
python scripts/init_admin.py
python manage.py runserver
```

### 本地启动前端

```bash
cd frontend
npm install
npm run dev
```

## 6. 数据库迁移命令

```bash
cd backend
python manage.py migrate
```

本阶段新增迁移：

```text
apps/users/migrations/0002_address.py
```

## 7. 测试命令

```bash
cd backend
python -m pytest apps/users/tests.py -v --ds=config.settings.test
```

## 8. 测试结果

```text
15 passed in 3.91s
```

覆盖：

- 用户注册（成功、密码不一致、邮箱重复）
- 用户登录（成功、密码错误、邮箱大小写不敏感）
- Token 刷新
- 未认证访问拦截
- 退出登录后 Refresh Token 失效
- 修改密码（成功、原密码错误）
- 收货地址新增
- 默认地址唯一性
- 地址越权访问返回 404

## 9. 常见错误和排查方法

| 现象 | 可能原因 | 解决 |
|------|----------|------|
| 测试报 `DisallowedHost` | `testserver` 不在 `ALLOWED_HOSTS` | 已在 `config/settings/test.py` 中设置 `ALLOWED_HOSTS = ["*"]` |
| 测试报 Redis 连接失败 | DRF throttle 默认使用 Redis cache | 测试环境改用 `LocMemCache` |
| 登录返回 500 | throttle 连接 Redis 失败 | 检查 Redis 是否已启动，或查看 `CELERY_BROKER_URL` |
| 注册报 `email` 唯一性冲突提示重复 | DRF 自动 UniqueValidator 与自定义校验冲突 | 已在 `extra_kwargs` 中关闭自动校验器 |
| 退出后仍能用旧 Refresh Token | `rest_framework_simplejwt.token_blacklist` 未迁移 | 执行 `python manage.py migrate` |

## 10. 本阶段仍未实现的内容

- 邮箱验证码注册/找回密码（开发环境仅打印邮件到控制台，业务接口未做）
- 用户头像上传
- 前端用户中心、收货地址管理页面
- 管理员/运营人员独立后台页面
- 角色权限的细粒度应用（IsAdmin/IsOperator 已创建，待商品/订单等模块使用）

## 11. 下一阶段计划

**阶段四：商品模块**

将实现：

- 商品分类（多级）与品牌
- SPU / SKU 模型与数据表关系
- 商品图片、属性、规格
- SKU 库存关联
- 商品列表、搜索、筛选、排序
- 商品详情页
