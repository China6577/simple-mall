<script setup></script>

<template>
  <div class="not-found">
    <div class="container not-found-inner">
      <div class="error-code">404</div>
      <h1 class="error-title">页面走丢了</h1>
      <p class="error-desc">抱歉，您访问的页面不存在或已被移除</p>
      <div class="error-actions">
        <el-button type="primary" size="large" @click="$router.push('/')">返回首页</el-button>
        <el-button size="large" plain @click="$router.push('/products')">浏览商品</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.not-found {
  padding: $space-16 0;
  text-align: center;
  background: $color-apple-gray;
  min-height: calc(100vh - 72px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.not-found-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.error-code {
  font-size: 140px;
  font-weight: 700;
  line-height: 1;
  color: $text-primary;
  letter-spacing: -0.06em;
  margin-bottom: $space-4;
}

.error-title {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: $space-3;
  color: $text-primary;
  letter-spacing: -0.02em;
}

.error-desc {
  font-size: 17px;
  color: $text-secondary;
  margin-bottom: $space-8;
}

.error-actions {
  display: flex;
  gap: $space-4;

  :deep(.el-button--primary) {
    background: $color-apple-blue;
    border: none;
    border-radius: $radius-full;
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 600;
    transition: all $transition-base;

    &:hover {
      background: $color-apple-blue-light;
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(0, 113, 227, 0.22);
    }
  }

  :deep(.el-button--default.is-plain) {
    border-radius: $radius-full;
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 600;
    border-color: $color-apple-border;
    color: $text-primary;
    transition: all $transition-base;

    &:hover {
      border-color: $color-apple-blue;
      color: $color-apple-blue;
      background: transparent;
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
  .not-found {
    padding: $space-10 0;
  }

  .error-code {
    font-size: 96px;
  }

  .error-title {
    font-size: 26px;
  }

  .error-desc {
    font-size: 15px;
  }

  .error-actions {
    flex-direction: column;
    width: 100%;
    padding: 0 $space-6;

    :deep(.el-button) {
      width: 100%;
    }
  }
}
</style>
