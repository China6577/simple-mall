<script setup>
defineProps({
  description: {
    type: String,
    default: '暂无数据'
  },
  actionText: {
    type: String,
    default: ''
  },
  actionLink: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <div class="empty-state">
    <div class="empty-illustration">
      <el-icon :size="56" class="empty-icon"><Box /></el-icon>
    </div>
    <p class="description">{{ description }}</p>
    <router-link v-if="actionText && actionLink" :to="actionLink" class="action-btn">
      {{ actionText }}
    </router-link>
  </div>
</template>

<style scoped lang="scss">
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $space-12 0;
  text-align: center;
}

.empty-illustration {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, $color-slate-100 0%, $color-slate-50 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-5;
}

.empty-icon {
  color: $color-slate-300;
}

.description {
  font-size: 15px;
  color: $text-secondary;
  font-weight: 500;
}

.action-btn {
  margin-top: $space-5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0 $space-6;
  border-radius: $radius-full;
  background: $color-apple-black;
  color: $color-apple-white;
  font-size: 15px;
  font-weight: 600;
  text-decoration: none;
  transition: all $transition-base;

  &:hover {
    background: $text-secondary;
    transform: translateY(-1px);
  }
}
</style>
