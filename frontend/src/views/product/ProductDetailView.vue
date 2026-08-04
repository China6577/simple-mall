<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import productApi from '@/api/product'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useUserStore } from '@/stores/user'
import { useCartStore } from '@/stores/cart'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const cartStore = useCartStore()

const product = ref(null)
const loading = ref(false)
const selectedSku = ref(null)
const quantity = ref(1)

const selectedSpecs = ref({})

const mainImage = computed(() => {
  return product.value?.main_image_url || product.value?.images?.[0]?.image || ''
})

const productImages = computed(() => {
  const images = []
  if (product.value?.main_image_url) images.push(product.value.main_image_url)
  if (product.value?.images?.length) {
    product.value.images.forEach((img) => {
      if (img.image && !images.includes(img.image)) images.push(img.image)
    })
  }
  return images.length ? images : []
})

const currentPrice = computed(() => {
  return selectedSku.value?.price || product.value?.skus?.[0]?.price || '暂无报价'
})

const availableStock = computed(() => {
  return selectedSku.value?.available_stock ?? selectedSku.value?.stock ?? 0
})

const activeImage = ref('')

function matchSku() {
  if (!product.value?.skus) return
  selectedSku.value = product.value.skus.find(
    (sku) => JSON.stringify(sku.specs) === JSON.stringify(selectedSpecs.value)
  ) || product.value.skus[0]
}

function onSpecChange(specName, optionValue) {
  selectedSpecs.value[specName] = optionValue
  matchSku()
}

function isSpecActive(specName, optionValue) {
  return selectedSpecs.value[specName] === optionValue
}

async function loadProduct() {
  const id = route.params.id
  if (!id) return

  loading.value = true
  try {
    const res = await productApi.getProductDetail(id)
    product.value = res
    if (product.value.skus?.length) {
      const defaultSku = product.value.skus.find((s) => s.is_default) || product.value.skus[0]
      selectedSpecs.value = { ...defaultSku.specs }
      selectedSku.value = defaultSku
    }
    activeImage.value = mainImage.value
  } catch (error) {
    console.error(error)
    product.value = null
  } finally {
    loading.value = false
  }
}

async function addToCart() {
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  if (!selectedSku.value) {
    ElMessage.warning('请选择商品规格')
    return
  }
  if (quantity.value > availableStock.value) {
    ElMessage.warning('库存不足')
    return
  }
  try {
    await cartStore.addToCart(selectedSku.value.id, quantity.value)
    ElMessage.success('已加入购物车')
  } catch (error) {
    console.error(error)
  }
}

function buyNow() {
  addToCart()
  router.push('/cart')
}

onMounted(loadProduct)
</script>

<template>
  <div class="product-detail-view">
    <div class="container">
      <Loading v-if="loading" />
      <EmptyState v-else-if="!product" description="商品不存在或已下架" />

      <div v-else class="detail-page">
        <!-- Breadcrumb -->
        <nav class="breadcrumb">
          <router-link to="/">首页</router-link>
          <el-icon><ArrowRight /></el-icon>
          <router-link to="/products">全部商品</router-link>
          <el-icon><ArrowRight /></el-icon>
          <span class="current">{{ product.name }}</span>
        </nav>

        <div class="detail-container">
          <!-- Gallery -->
          <div class="gallery">
            <div class="main-image-wrapper">
              <img v-if="activeImage" :src="activeImage" class="main-image" />
              <div v-else class="main-image placeholder">暂无图片</div>
            </div>
            <div v-if="productImages.length > 1" class="thumbnail-list">
              <button
                v-for="(img, idx) in productImages"
                :key="idx"
                class="thumbnail"
                :class="{ active: activeImage === img }"
                @click="activeImage = img"
              >
                <img :src="img" />
              </button>
            </div>
          </div>

          <!-- Info -->
          <div class="info">
            <div class="info-header">
              <h1 class="name">{{ product.name }}</h1>
              <p class="desc">{{ product.description }}</p>
            </div>

            <div class="price-card">
              <div class="price-main">
                <span class="price-label">售价</span>
                <span class="price">
                  <span class="currency">¥</span>{{ currentPrice }}
                </span>
              </div>
              <div class="price-meta">
                <span class="stock">
                  <el-icon><Box /></el-icon>
                  库存 {{ availableStock }} 件
                </span>
                <span class="sales">已售 {{ product.sales || 0 }}</span>
              </div>
            </div>

            <!-- Specs -->
            <div v-for="spec in product.specs" :key="spec.id" class="spec-row">
              <span class="spec-name">{{ spec.name }}</span>
              <div class="spec-options">
                <button
                  v-for="opt in spec.options"
                  :key="opt.id"
                  class="spec-btn"
                  :class="{ active: isSpecActive(spec.name, opt.value) }"
                  @click="onSpecChange(spec.name, opt.value)"
                >
                  {{ opt.value }}
                </button>
              </div>
            </div>

            <div class="quantity-row">
              <span class="quantity-label">数量</span>
              <el-input-number v-model="quantity" :min="1" :max="availableStock" />
              <span v-if="selectedSku" class="selected-sku">已选：{{ selectedSku.sku_code }}</span>
            </div>

            <div class="actions">
              <el-button type="primary" size="large" class="cart-btn" @click="addToCart">
                <el-icon><ShoppingCart /></el-icon>
                加入购物车
              </el-button>
              <el-button size="large" class="buy-btn" @click="buyNow">
                立即购买
              </el-button>
            </div>

            <div class="service-tags">
              <div class="tag">
                <el-icon><CircleCheck /></el-icon>
                <span>正品保障</span>
              </div>
              <div class="tag">
                <el-icon><Van /></el-icon>
                <span>极速发货</span>
              </div>
              <div class="tag">
                <el-icon><RefreshLeft /></el-icon>
                <span>7天无理由</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.product-detail-view {
  padding: $space-8 0 $space-20;
  background: $bg-body;
}

.container {
  width: 100%;
  max-width: 1080px;
  margin: 0 auto;
  padding: 0 $space-6;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: 13px;
  color: $text-secondary;
  margin-bottom: $space-8;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;

  a {
    color: $text-secondary;
    transition: color $transition-fast;

    &:hover {
      color: $text-primary;
    }
  }

  .current {
    color: $text-primary;
    font-weight: 500;
  }

  .el-icon {
    font-size: 12px;
    color: $text-tertiary;
  }
}

.detail-container {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: $space-10;
  background: $color-apple-white;
  padding: $space-8;
  border-radius: $radius-xl;
  border: 1px solid $border-light;
  box-shadow: $shadow-md;
  animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

// Gallery
.gallery {
  display: flex;
  flex-direction: column;
  gap: $space-5;
}

.main-image-wrapper {
  background: $color-apple-gray;
  border-radius: $radius-xl;
  overflow: hidden;
  aspect-ratio: 1 / 1;
}

.main-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform $transition-slow;

  &:hover {
    transform: scale(1.03);
  }

  &.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    color: $text-secondary;
    font-size: 16px;
  }
}

.thumbnail-list {
  display: flex;
  gap: $space-3;
  overflow-x: auto;
  padding-bottom: $space-2;
}

.thumbnail {
  width: 76px;
  height: 76px;
  border-radius: $radius-lg;
  overflow: hidden;
  border: 2px solid transparent;
  background: $color-apple-gray;
  cursor: pointer;
  padding: 0;
  transition: all $transition-fast;
  flex-shrink: 0;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &:hover {
    border-color: $color-apple-border;
  }

  &.active {
    border-color: $color-apple-black;
    box-shadow: 0 0 0 3px rgba($color-apple-black, 0.12);
  }
}

// Info
.info {
  display: flex;
  flex-direction: column;
  gap: $space-6;
}

.info-header {
  .name {
    font-family: $font-display;
    font-size: 30px;
    font-weight: 700;
    line-height: 1.25;
    letter-spacing: -0.03em;
    margin-bottom: $space-3;
    color: $text-primary;
  }

  .desc {
    font-size: 15px;
    color: $text-secondary;
    line-height: 1.6;
  }
}

.price-card {
  background: $color-apple-gray;
  border-radius: $radius-xl;
  padding: $space-6;
}

.price-main {
  display: flex;
  align-items: baseline;
  gap: $space-3;
  margin-bottom: $space-4;
}

.price-label {
  font-size: 13px;
  color: $text-secondary;
  font-weight: 500;
}

.price {
  font-size: 36px;
  font-weight: 700;
  color: $text-primary;
  letter-spacing: -0.03em;

  .currency {
    font-size: 22px;
    font-weight: 600;
    margin-right: 4px;
  }
}

.price-meta {
  display: flex;
  align-items: center;
  gap: $space-6;
  font-size: 13px;
  color: $text-secondary;

  .stock {
    display: flex;
    align-items: center;
    gap: $space-2;
  }
}

.spec-row {
  display: flex;
  align-items: flex-start;
  gap: $space-5;
}

.spec-name {
  width: 64px;
  flex-shrink: 0;
  font-size: 14px;
  color: $text-secondary;
  font-weight: 500;
  padding-top: 10px;
}

.spec-options {
  display: flex;
  gap: $space-3;
  flex-wrap: wrap;
}

.spec-btn {
  min-width: 80px;
  padding: 10px 18px;
  border-radius: $radius-full;
  border: 1px solid $color-apple-border;
  background: $color-apple-white;
  color: $text-primary;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    border-color: $color-apple-black;
  }

  &.active {
    background: $color-apple-black;
    border-color: $color-apple-black;
    color: $color-apple-white;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.15);
  }
}

.quantity-row {
  display: flex;
  align-items: center;
  gap: $space-5;
  flex-wrap: wrap;

  :deep(.el-input-number) {
    width: 130px;

    .el-input__wrapper {
      background: $color-apple-white;
      border-radius: $radius-md;
      box-shadow: 0 0 0 1px $color-apple-border inset;
      padding: 0;
      transition: box-shadow $transition-fast;
    }

    &:hover .el-input__wrapper,
    .el-input-number__decrease:hover ~ .el-input__wrapper,
    .el-input-number__increase:hover ~ .el-input__wrapper {
      box-shadow: 0 0 0 2px $color-apple-blue inset;
    }

    .el-input-number__decrease,
    .el-input-number__increase {
      width: 34px;
      background: transparent;
      border-color: transparent;
      color: $text-secondary;
      transition: all $transition-fast;

      &:hover {
        color: $color-apple-blue;
        background: $color-apple-blue-soft;
      }

      &.is-disabled {
        color: $text-tertiary;
        background: transparent;
      }
    }

    .el-input__inner {
      font-size: 15px;
      font-weight: 600;
      color: $text-primary;
    }
  }
}

.quantity-label {
  font-size: 14px;
  color: $text-secondary;
  font-weight: 500;
}

.selected-sku {
  font-size: 13px;
  color: $text-secondary;
}

.actions {
  display: flex;
  gap: $space-4;
  padding-top: $space-2;

  .el-button {
    flex: 1;
    height: 48px;
    font-size: 16px;
    font-weight: 600;
    border-radius: $radius-full;
    transition: transform $transition-base, box-shadow $transition-base;

    &:hover {
      transform: scale(1.02);
    }

    :deep(.el-icon) {
      margin-right: $space-2;
    }
  }

  .cart-btn {
    background: $color-apple-black;
    border-color: $color-apple-black;
    color: $color-apple-white;

    &:hover {
      background: #1d1d1f;
      border-color: #1d1d1f;
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.18);
    }
  }

  .buy-btn {
    background: $color-apple-blue;
    border-color: $color-apple-blue;
    color: $color-apple-white;

    &:hover {
      background: $color-apple-blue-light;
      border-color: $color-apple-blue-light;
      box-shadow: 0 8px 24px rgba(0, 113, 227, 0.28);
    }
  }
}

.service-tags {
  display: flex;
  gap: $space-6;
  padding-top: $space-6;
  border-top: 1px solid $border-light;
  flex-wrap: wrap;
}

.tag {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: 14px;
  color: $text-secondary;

  .el-icon {
    color: $color-apple-blue;
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

@media (max-width: 1024px) {
  .detail-container {
    grid-template-columns: 1fr;
    gap: $space-8;
  }

  .gallery {
    max-width: 480px;
    margin: 0 auto;
  }
}

@media (max-width: 768px) {
  .detail-container {
    padding: $space-6;
  }

  .info-header .name {
    font-size: 28px;
  }

  .price {
    font-size: 36px;
  }

  .actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 $space-4;
  }

  .detail-container {
    padding: $space-5;
  }

  .breadcrumb {
    font-size: 12px;
    margin-bottom: $space-5;
  }

  .info-header .name {
    font-size: 24px;
  }

  .price {
    font-size: 32px;

    .currency {
      font-size: 22px;
    }
  }

  .price-card {
    padding: $space-5;
  }

  .spec-name {
    width: 52px;
  }

  .thumbnail {
    width: 64px;
    height: 64px;
  }
}
</style>
