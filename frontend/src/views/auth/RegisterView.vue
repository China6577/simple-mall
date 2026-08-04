<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import authApi from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'

const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const loading = ref(false)

const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: [] }],
  email: [{ required: true, message: '请输入邮箱', trigger: [] }],
  password: [
    { required: true, message: '请输入密码', trigger: [] },
    { min: 8, message: '密码长度不能少于8位', trigger: [] }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: [] },
    { validator: validatePass, trigger: [] }
  ]
}

const formRef = ref()

async function onSubmit() {
  await formRef.value.validate()
  // 校验通过后立即清除校验状态，避免跳转前输入框出现 success 样式变化
  formRef.value.clearValidate()
  loading.value = true
  try {
    const payload = {
      username: form.username,
      email: form.email,
      password: form.password,
      confirm_password: form.confirmPassword
    }
    const data = await authApi.register(payload)
    userStore.setTokens(data.access, data.refresh)
    userStore.setUser(data.user)
    // 重新加载当前用户购物车，避免 Header badge 残留旧账号数据
    await cartStore.loadCart()
    ElMessage.success('注册成功')
    // 注册成功后直接跳转到个人中心
    await router.push('/profile')
  } catch {
    // request.js 已统一提示错误；这里只需恢复按钮状态
    loading.value = false
  }
}
</script>

<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-visual">
        <div class="brand">
          <span class="logo-text">SimpleMall</span>
        </div>
        <h2 class="visual-title">加入 SimpleMall</h2>
        <p class="visual-desc">注册即可领取新人大礼包，畅享品质购物体验</p>
        <div class="feature-list">
          <div class="feature">
            <el-icon><CircleCheck /></el-icon>
            <span>专属优惠</span>
          </div>
          <div class="feature">
            <el-icon><Van /></el-icon>
            <span>极速发货</span>
          </div>
          <div class="feature">
            <el-icon><RefreshLeft /></el-icon>
            <span>无忧售后</span>
          </div>
        </div>
      </div>

      <div class="auth-form-wrapper">
        <div class="auth-card">
          <h2 class="form-title">创建账号</h2>
          <p class="form-subtitle">填写以下信息完成注册</p>

          <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="auth-form">
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="form.username"
                name="username"
                placeholder="请输入用户名"
                size="large"
                autocomplete="username"
              />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input
                v-model="form.email"
                name="email"
                placeholder="请输入邮箱"
                size="large"
                autocomplete="email"
              />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input
                v-model="form.password"
                name="password"
                type="password"
                placeholder="请输入密码"
                show-password
                size="large"
                autocomplete="new-password"
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="form.confirmPassword"
                name="confirmPassword"
                type="password"
                placeholder="请再次输入密码"
                show-password
                size="large"
                autocomplete="new-password"
                @keyup.enter="onSubmit"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" size="large" :loading="loading" class="submit-btn" @click="onSubmit">
                注册
              </el-button>
            </el-form-item>
          </el-form>

          <div class="auth-footer">
            <span>已有账号？</span>
            <router-link to="/login" class="auth-link">立即登录</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>

</template>

<style scoped lang="scss">
.auth-page {
  min-height: calc(100vh - 72px);
  display: flex;
  align-items: center;
  justify-content: center;
  background: $color-apple-gray;
  padding: $space-8 $container-padding;
}

.auth-container {
  display: grid;
  grid-template-columns: 1fr 440px;
  max-width: 980px;
  width: 100%;
  background: $color-apple-white;
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-lg;
  animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.auth-visual {
  background: $color-apple-gray-light;
  color: $text-primary;
  padding: $space-12;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    top: -40%;
    right: -40%;
    width: 90%;
    height: 90%;
    background: radial-gradient(circle, rgba(0, 113, 227, 0.08) 0%, transparent 70%);
  }
}

.brand {
  display: flex;
  align-items: center;
  gap: $space-3;
  margin-bottom: $space-10;
  position: relative;
  z-index: 1;

  .logo-text {
    font-family: $font-display;
    font-size: 26px;
    font-weight: 600;
    letter-spacing: -0.02em;
  }
}

.visual-title {
  font-size: 34px;
  font-weight: 700;
  line-height: 1.15;
  margin-bottom: $space-4;
  color: $text-primary;
  position: relative;
  z-index: 1;
  letter-spacing: -0.03em;
}

.visual-desc {
  font-size: 16px;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: $space-10;
  position: relative;
  z-index: 1;
}

.feature-list {
  display: flex;
  flex-direction: column;
  gap: $space-5;
  position: relative;
  z-index: 1;
}

.feature {
  display: flex;
  align-items: center;
  gap: $space-3;
  font-size: 15px;
  color: $text-secondary;
  font-weight: 500;

  .el-icon {
    color: $color-apple-blue;
    font-size: 18px;
  }
}

.auth-form-wrapper {
  padding: $space-12;
  display: flex;
  align-items: center;
  justify-content: center;
}

.auth-card {
  width: 100%;
  border: none;
  box-shadow: none;
  background: transparent;
}

.form-title {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: $space-2;
  letter-spacing: -0.03em;
}

.form-subtitle {
  font-size: 15px;
  color: $text-secondary;
  margin-bottom: $space-8;
}

.auth-form {
  .el-form-item {
    margin-bottom: $space-5;
  }

  :deep(.el-form-item__label) {
    font-weight: 500;
    color: $text-primary;
    padding-bottom: $space-2;
    font-size: 14px;
  }

  :deep(.el-input__wrapper) {
    border-radius: $radius-md;
    box-shadow: 0 0 0 1px $color-apple-border inset;
    padding: 4px 12px;
    transition: box-shadow $transition-base;

    &:hover,
    &.is-focus {
      box-shadow: 0 0 0 2px $color-apple-blue inset;
    }
  }

  :deep(.el-input__inner) {
    height: 40px;
    font-size: 15px;
  }

  .submit-btn {
    width: 100%;
    height: 52px;
    font-size: 17px;
    font-weight: 600;
    border-radius: $radius-full;
    margin-top: $space-2;
    background: $color-apple-blue;
    border: none;
    transition: all $transition-base;

    &:hover {
      background: $color-apple-blue-light;
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(0, 113, 227, 0.25);
    }
  }
}

.auth-footer {
  text-align: center;
  margin-top: $space-8;
  font-size: 15px;
  color: $text-secondary;

  .auth-link {
    color: $color-apple-blue;
    font-weight: 600;
    margin-left: $space-2;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(24px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .auth-page {
    padding: $space-5 $container-padding;
    background: $color-apple-white;
  }

  .auth-container {
    grid-template-columns: 1fr;
    box-shadow: none;
    border-radius: 0;
    animation: none;
  }

  .auth-visual {
    display: none;
  }

  .auth-form-wrapper {
    padding: $space-6 $space-4;
  }

  .form-title {
    font-size: 26px;
  }
}
</style>
