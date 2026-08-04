<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Loading,
  Search,
  Document,
  Ticket,
  Setting,
  ShoppingCart,
  UserFilled,
} from '@element-plus/icons-vue'
import authApi from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'
import storage from '@/utils/storage'

const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()
const isLoggingOut = ref(false)

onMounted(() => {
  if (userStore.isLoggedIn) {
    cartStore.loadCart()
  }
})
const searchKeyword = ref('')

async function logout() {
  isLoggingOut.value = true
  try {
    await authApi.logout(storage.getRefreshToken())
    ElMessage.success('已退出登录')
  } catch (error) {
    console.error('Logout failed', error)
  } finally {
    userStore.logout()
    window.location.href = '/login'
  }
}

function onSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return
  router.push({ path: '/search', query: { keyword } })
}
</script>

<template>
  <header class="app-header">
    <div class="container header-inner">
      <router-link to="/" class="logo">
        <span class="logo-text">SimpleMall</span>
      </router-link>

      <nav class="main-nav">
        <router-link to="/" class="nav-link" active-class="">首页</router-link>
        <router-link to="/products" class="nav-link">全部商品</router-link>
      </nav>

      <div class="search-box">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索心仪商品..."
          clearable
          size="large"
          @keyup.enter="onSearch"
        >
          <template #suffix>
            <button class="search-btn" type="button" @click="onSearch">
              <el-icon><Search /></el-icon>
            </button>
          </template>
        </el-input>
      </div>

      <div class="user-area">
        <router-link v-if="userStore.isLoggedIn" to="/orders" class="icon-link">
          <el-icon :size="20"><Document /></el-icon>
          <span>订单</span>
        </router-link>
        <router-link v-if="userStore.isLoggedIn" to="/coupons" class="icon-link">
          <el-icon :size="20"><Ticket /></el-icon>
          <span>优惠券</span>
        </router-link>
        <a v-if="userStore.isAdmin" href="/admin/" target="_blank" class="icon-link">
          <el-icon :size="20"><Setting /></el-icon>
          <span>后台</span>
        </a>

        <router-link to="/cart" class="cart-link">
          <el-badge :value="cartStore.totalCount" :hidden="cartStore.totalCount === 0" type="danger">
            <el-icon :size="22"><ShoppingCart /></el-icon>
          </el-badge>
          <span>购物车</span>
        </router-link>

        <template v-if="userStore.isLoggedIn">
          <router-link to="/profile" class="user-profile">
            <el-avatar
              v-if="userStore.userInfo?.avatar_url"
              :size="32"
              :src="userStore.userInfo.avatar_url"
              class="user-avatar"
            />
            <el-avatar
              v-else
              :size="32"
              :icon="UserFilled"
              class="user-avatar"
            />
            <span class="username">{{ userStore.userInfo?.username || '用户' }}</span>
          </router-link>
          <el-button link class="logout-btn" @click="logout">退出</el-button>
        </template>
        <template v-else>
          <router-link to="/login" class="login-link">登录</router-link>
          <router-link to="/register" class="register-btn">注册</router-link>
        </template>
      </div>
    </div>
  </header>

  <div v-if="isLoggingOut" class="logout-overlay">
    <el-icon class="logout-spin" :size="32"><Loading /></el-icon>
    <span>正在退出...</span>
  </div>
</template>

<style scoped lang="scss">
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}

.header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 52px;
  gap: $space-8;
}

.logo {
  display: flex;
  align-items: center;
  gap: $space-3;
  flex-shrink: 0;

  .logo-text {
    font-family: $font-display;
    font-size: 21px;
    font-weight: 700;
    color: $text-primary;
    letter-spacing: -0.04em;
  }
}

.main-nav {
  display: flex;
  align-items: center;
  gap: $space-8;
  flex-shrink: 0;

  .nav-link {
    position: relative;
    font-size: 13px;
    font-weight: 500;
    color: $text-primary;
    padding: $space-2 0;
    letter-spacing: -0.01em;
    transition: opacity $transition-fast;
    opacity: 0.8;

    &:hover {
      opacity: 1;
    }

    &.router-link-active,
    &.router-link-exact-active {
      opacity: 1;
      font-weight: 600;
    }
  }
}

.search-box {
  flex: 1;
  max-width: 360px;

  :deep(.el-input__wrapper) {
    border-radius: $radius-full;
    background: rgba(0, 0, 0, 0.04);
    box-shadow: none;
    padding: 4px 8px 4px 18px;
    height: 36px;

    &:hover, &.is-focus {
      background: rgba(0, 0, 0, 0.06);
      box-shadow: none;
    }
  }

  :deep(.el-input__inner) {
    font-size: 13px;
    color: $text-primary;

    &::placeholder {
      color: $text-secondary;
    }
  }

  :deep(.el-input__suffix-inner) {
    display: flex;
    align-items: center;
    gap: $space-2;
    padding-right: 4px;
  }

  :deep(.el-input__clear) {
    position: relative;
    color: $text-secondary;
    font-size: 16px;
    margin-right: 2px;

    &:hover {
      color: $text-primary;
    }
  }

  .search-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: $radius-full;
    background: transparent;
    color: $text-secondary;
    border: none;
    cursor: pointer;
    transition: color $transition-fast;

    &:hover {
      color: $text-primary;
    }

    .el-icon {
      font-size: 16px;
    }
  }
}

.user-area {
  display: flex;
  align-items: center;
  gap: $space-5;
  flex-shrink: 0;
  padding-right: $space-3;

  .icon-link,
  .cart-link {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    font-size: 11px;
    color: $text-primary;
    opacity: 0.8;
    transition: opacity $transition-fast;

    &:hover {
      opacity: 1;
    }
  }

  .cart-link {
    position: relative;
    padding-right: 18px;

    :deep(.el-badge__content) {
      top: 6px;
      right: 2px;
      border: 2px solid rgba(255, 255, 255, 0.85);
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
      font-size: 10px;
      font-weight: 700;
      min-width: 18px;
      height: 18px;
      padding: 0 4px;
      line-height: 14px;
    }
  }

  .user-profile {
    display: flex;
    align-items: center;
    gap: $space-2;
    padding-left: $space-4;
    border-left: 1px solid $border-color;

    .user-avatar {
      background: $color-primary-soft;
      color: $color-primary;
    }

    .username {
      font-size: 13px;
      font-weight: 500;
      color: $text-primary;
    }
  }

  .logout-btn {
    color: $text-secondary;
    font-size: 13px;

    &:hover {
      color: $color-danger;
    }
  }

  .login-link {
    font-size: 13px;
    font-weight: 500;
    color: $text-primary;
    opacity: 0.8;

    &:hover {
      opacity: 1;
    }
  }

  .register-btn {
    font-size: 13px;
    font-weight: 500;
    color: white;
    background: $color-apple-blue;
    padding: 7px 16px;
    border-radius: $radius-full;
    transition: all $transition-fast;

    &:hover {
      background: $color-apple-blue-light;
      transform: scale(1.03);
    }
  }
}

@media (max-width: 1024px) {
  .main-nav {
    display: none;
  }

  .search-box {
    max-width: none;
  }
}

@media (max-width: 768px) {
  .header-inner {
    flex-wrap: wrap;
    height: auto;
    padding: $space-3 $container-padding;
    gap: $space-3;
  }

  .search-box {
    order: 3;
    width: 100%;
  }

  .user-area {
    gap: $space-4;

    .icon-link span,
    .cart-link span {
      display: none;
    }

    .user-profile .username {
      display: none;
    }
  }
}

.logout-overlay {
  position: fixed;
  inset: 0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $space-3;
  color: $text-secondary;
  font-size: 14px;
}

.logout-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
