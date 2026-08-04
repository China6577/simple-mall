<script setup>
defineProps({
  text: {
    type: String,
    default: '加载中...'
  }
})
</script>

<template>
  <div class="loading">
    <div class="spinner">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <p>{{ text }}</p>
  </div>
</template>

<style scoped lang="scss">
.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $space-12;
  color: $text-secondary;
  gap: $space-5;

  p {
    font-size: 14px;
    font-weight: 500;
  }
}

.spinner {
  position: relative;
  width: 48px;
  height: 48px;
}

.spinner-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 3px solid transparent;
  border-top-color: $color-primary;
  animation: spin 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;

  &:nth-child(1) {
    animation-delay: -0.45s;
  }

  &:nth-child(2) {
    animation-delay: -0.3s;
    border-top-color: $color-primary-light;
  }

  &:nth-child(3) {
    animation-delay: -0.15s;
    border-top-color: rgba(37, 99, 235, 0.4);
  }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
