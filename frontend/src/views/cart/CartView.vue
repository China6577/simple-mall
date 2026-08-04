<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCartStore } from '@/stores/cart'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const cartStore = useCartStore()

onMounted(() => {
  cartStore.loadCart()
})

async function onSelectItem(item) {
  await cartStore.updateItem(item.id, { selected: item.selected })
}

async function onQuantityChange(item, value) {
  if (value < 1) return
  await cartStore.updateItem(item.id, { quantity: value })
}

async function onRemove(item) {
  try {
    await ElMessageBox.confirm('确定从购物车删除该商品吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await cartStore.removeItem(item.id)
    ElMessage.success('已删除')
  } catch (error) {
    console.error(error)
  }
}

async function onSelectAll(value) {
  await cartStore.selectAll(value)
}

function onCheckout() {
  if (cartStore.selectedCount === 0) {
    ElMessage.warning('请至少选择一件商品')
    return
  }
  const ids = cartStore.selectedItems.map((item) => item.id).join(',')
  router.push({ path: '/order/confirm', query: { ids } })
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}
</script>

<template>
  <div class="cart-view">
    <div class="container">
      <div class="page-header fade-in-up">
        <h1 class="page-title">购物车</h1>
        <p class="page-subtitle">共 {{ cartStore.totalCount }} 件商品</p>
      </div>

      <Loading v-if="cartStore.loading" />
      <EmptyState
        v-else-if="cartStore.items.length === 0"
        description="购物车还是空的"
        action-text="去商店逛逛"
        action-link="/products"
      />

      <div v-else class="cart-layout">
        <div class="cart-main card-elevated fade-in-up" style="animation-delay: 80ms">
          <div class="cart-header">
            <el-checkbox
              :model-value="cartStore.isAllSelected"
              label="全选"
              size="large"
              @update:model-value="onSelectAll"
            />
            <span class="col-product">商品信息</span>
            <span class="col-quantity">数量</span>
            <span class="col-subtotal">小计</span>
            <span class="col-action">操作</span>
          </div>

          <div class="cart-items">
            <div v-for="(item, index) in cartStore.items" :key="item.id" class="cart-item" :style="{ animationDelay: `${120 + index * 60}ms` }">
              <el-checkbox v-model="item.selected" @change="onSelectItem(item)" />

              <div class="product-info">
                <img
                  :src="item.spu_main_image || item.sku?.spu?.main_image_url || ''"
                  class="product-image"
                  alt="商品图片"
                />
                <div class="product-meta">
                  <p class="product-name">{{ item.spu_name }}</p>
                  <p class="product-specs">{{ Object.values(item.sku?.specs || {}).join(' / ') }}</p>
                  <p class="product-unit-price">
                    <span class="price-label">单价</span>
                    ¥{{ formatPrice(item.sku?.price) }}
                  </p>
                </div>
              </div>

              <div class="col-quantity">
                <el-input-number
                  v-model="item.quantity"
                  :min="1"
                  :max="item.sku?.available_stock || item.sku?.stock || 999"
                  size="small"
                  @change="(value) => onQuantityChange(item, value)"
                />
              </div>

              <div class="col-subtotal">¥{{ formatPrice(item.subtotal) }}</div>

              <div class="col-action">
                <el-button link type="danger" class="delete-btn" @click="onRemove(item)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </div>
        </div>

        <div class="cart-summary">
          <div class="summary-card card-elevated fade-in-up" style="animation-delay: 160ms">
            <h3 class="summary-title">订单摘要</h3>
            <div class="summary-row">
              <span>商品总数</span>
              <span>{{ cartStore.selectedCount }} 件</span>
            </div>
            <div class="summary-row">
              <span>商品总额</span>
              <span>¥{{ formatPrice(cartStore.totalAmount) }}</span>
            </div>
            <div class="summary-row">
              <span>运费</span>
              <span class="free">免运费</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-row total">
              <span>应付总额</span>
              <span class="total-price">¥{{ formatPrice(cartStore.totalAmount) }}</span>
            </div>
            <el-button type="primary" size="large" class="checkout-btn" @click="onCheckout">
              去结算
            </el-button>
            <p class="checkout-tip">已选 {{ cartStore.selectedCount }} 件商品</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.cart-view {
  padding: $space-10 0 $space-20;
  background: $color-apple-gray;
  min-height: 100vh;
}

.page-header {
  margin-bottom: $space-8;
}

.page-title {
  font-family: $font-display;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: $text-primary;
  margin-bottom: $space-2;
}

.page-subtitle {
  font-size: 15px;
  color: $text-secondary;
  font-weight: 400;
}

.card-elevated {
  background: $color-apple-white;
  border-radius: $radius-xl;
  box-shadow: $shadow-md;
  border: 1px solid $color-apple-border-light;
}

.cart-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: $space-8;
  align-items: start;
}

.cart-main {
  overflow: hidden;
}

.cart-header,
.cart-item {
  display: grid;
  grid-template-columns: 50px 2fr 140px 140px 60px;
  align-items: center;
  padding: $space-5 $space-6;
  gap: $space-4;
}

.cart-header {
  background: $color-apple-gray;
  color: $text-secondary;
  font-size: 13px;
  font-weight: 600;
  border-bottom: 1px solid $border-light;
}

.cart-items {
  padding: $space-2 $space-2;
}

.cart-item {
  border-bottom: 1px solid $border-light;
  transition: box-shadow $transition-fast;
  opacity: 0;
  animation: fadeInUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;

  &:hover {
    box-shadow: inset 0 0 0 1px $border-light;
  }

  &:last-child {
    border-bottom: none;
  }
}

.col-product,
.product-info {
  text-align: left;
}

.col-price,
.col-quantity,
.col-subtotal,
.col-action {
  text-align: center;
}

.product-info {
  display: flex;
  gap: $space-5;
  align-items: center;
}

.product-image {
  width: 96px;
  height: 96px;
  object-fit: cover;
  border-radius: $radius-lg;
  background: $color-apple-gray;
}

.product-meta {
  .product-name {
    font-size: 16px;
    font-weight: 600;
    color: $text-primary;
    margin-bottom: $space-2;
    letter-spacing: -0.01em;
  }

  .product-specs {
    font-size: 14px;
    color: $text-secondary;
    font-weight: 400;
    margin-bottom: $space-2;
  }

  .product-unit-price {
    font-size: 14px;
    font-weight: 600;
    color: $text-primary;
    letter-spacing: -0.01em;

    .price-label {
      font-size: 12px;
      font-weight: 500;
      color: $text-secondary;
      margin-right: $space-1;
    }
  }
}

.col-subtotal {
  color: $text-primary;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.01em;
}

.delete-btn {
  color: $text-secondary;

  &:hover {
    color: $color-danger;
  }
}

// Summary
.cart-summary {
  position: sticky;
  top: 96px;
}

.summary-card {
  padding: $space-8;
}

.summary-title {
  font-family: $font-display;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: $space-6;
  color: $text-primary;
  letter-spacing: -0.02em;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-4;
  font-size: 15px;
  color: $text-secondary;

  .free {
    color: $color-success;
    font-weight: 600;
  }

  &.total {
    font-size: 16px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: 0;

    .total-price {
      font-size: 32px;
      font-weight: 800;
      color: $text-primary;
      letter-spacing: -0.03em;
    }
  }
}

.summary-divider {
  height: 1px;
  background: $border-light;
  margin: $space-6 0;
}

.checkout-btn {
  width: 100%;
  height: 54px;
  font-size: 16px;
  font-weight: 600;
  border-radius: $radius-full;
  margin-top: $space-6;
  background: $color-apple-black;
  border-color: $color-apple-black;
  transition: transform $transition-fast, box-shadow $transition-fast;

  &:hover {
    transform: scale(1.02);
    box-shadow: $shadow-lg;
    background: $color-apple-black;
    border-color: $color-apple-black;
  }

  &:active {
    transform: scale(0.98);
  }
}

.checkout-tip {
  text-align: center;
  font-size: 13px;
  color: $text-secondary;
  margin-top: $space-3;
}

.fade-in-up {
  opacity: 0;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) forwards;
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

@media (max-width: 1024px) {
  .cart-layout {
    grid-template-columns: 1fr;
  }

  .cart-summary {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 32px;
  }

  .cart-header,
  .cart-item {
    grid-template-columns: 40px 1fr 60px;
  }

  .cart-header .col-quantity,
  .cart-header .col-subtotal {
    display: none;
  }

  .cart-item {
    .col-quantity,
    .col-subtotal {
      display: none;
    }
  }

  .product-image {
    width: 72px;
    height: 72px;
  }
}
</style>
