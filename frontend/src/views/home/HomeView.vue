<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import productApi from '@/api/product'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const products = ref([])
const loading = ref(false)
const categoryMap = ref({})

onMounted(async () => {
  loading.value = true
  try {
    const [productRes, categoryRes] = await Promise.all([
      productApi.getProducts({ page_size: 8 }),
      productApi.getCategories()
    ])
    products.value = productRes.results || []
    ;(categoryRes || []).forEach((cat) => {
      categoryMap.value[cat.name] = cat.id
    })
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
})

function goToDetail(id) {
  router.push(`/products/${id}`)
}

function goToProducts() {
  router.push('/products')
}

function goToCategory(cat) {
  const id = categoryMap.value[cat.name]
  if (id) {
    router.push({ path: '/products', query: { category: String(id) } })
  } else {
    router.push({ path: '/products', query: { keyword: cat.name } })
  }
}

const categories = [
  { name: '手机通讯', icon: 'Phone', color: '#3b82f6' },
  { name: '电脑办公', icon: 'Monitor', color: '#8b5cf6' },
  { name: '智能穿戴', icon: 'Watch', color: '#06b6d4' },
  { name: '数码配件', icon: 'Headset', color: '#f59e0b' },
]
</script>

<template>
  <div class="home-view">
    <!-- Hero Banner -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">新品上市</div>
        <h1 class="hero-title">
          <span class="title-line">探索品质生活</span>
          <span class="title-line accent">从 SimpleMall 开始</span>
        </h1>
        <p class="hero-desc">精选全球优质好物，为企业与个人提供极致购物体验。</p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="goToProducts">立即选购</el-button>
          <el-button size="large" class="hero-secondary" @click="goToProducts">浏览全部</el-button>
        </div>
      </div>
      <div class="hero-visual">
        <div class="hero-glow"></div>
        <div class="hero-product">
          <img src="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&h=600&fit=crop" alt="Featured product" />
        </div>
      </div>
    </section>

    <!-- Categories -->
    <section class="categories-section">
      <div class="container">
        <h2 class="section-title">热门分类</h2>
        <div class="category-grid">
          <div v-for="cat in categories" :key="cat.name" class="category-card" @click="goToCategory(cat)">
            <div class="category-icon" :style="{ background: `linear-gradient(135deg, ${cat.color}22 0%, ${cat.color}0d 100%)`, color: cat.color }">
              <el-icon :size="28"><component :is="cat.icon" /></el-icon>
            </div>
            <span class="category-name">{{ cat.name }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Products -->
    <section class="products-section">
      <div class="container">
        <div class="section-header">
          <h2 class="section-title">热门推荐</h2>
          <router-link to="/products" class="view-all">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </router-link>
        </div>

        <Loading v-if="loading" />
        <EmptyState v-else-if="products.length === 0" description="商品正在上架中" />

        <div v-else class="product-grid">
          <div
            v-for="item in products"
            :key="item.id"
            class="product-card"
            @click="goToDetail(item.id)"
          >
            <div class="product-image-wrapper">
              <img v-if="item.main_image_url" :src="item.main_image_url" class="product-image" />
              <div v-else class="product-image placeholder">暂无图片</div>
            </div>
            <div class="product-info">
              <h3 class="product-name">{{ item.name }}</h3>
              <p class="product-desc">{{ item.description || '精选好物，品质保障' }}</p>
              <div class="product-footer">
                <span class="product-price">
                  <span class="currency">¥</span>{{ item.default_sku?.price || '暂无报价' }}
                </span>
                <span class="product-sales">已售 {{ item.sales || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped lang="scss">
.home-view {
  padding-bottom: $space-20;
}

// Hero Section - Apple 风格大留白
.hero-section {
  position: relative;
  background: $color-apple-gray;
  overflow: hidden;
  display: grid;
  grid-template-columns: 1fr 1fr;
  align-items: center;
  min-height: calc(100vh - 52px);
  max-height: 900px;
  margin-bottom: $space-16;
}

.hero-content {
  padding: $space-16 6vw $space-16 8vw;
  max-width: 640px;
  animation: fadeInUp 0.8s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: $space-2;
  background: rgba(0, 0, 0, 0.06);
  color: $text-primary;
  font-size: 12px;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: $radius-full;
  margin-bottom: $space-6;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.hero-title {
  font-size: clamp(40px, 4.5vw, 64px);
  font-weight: 700;
  line-height: 1.08;
  letter-spacing: -0.04em;
  margin-bottom: $space-5;
  color: $text-primary;

  .title-line {
    display: block;

    &.accent {
      color: $color-apple-blue;
    }
  }
}

.hero-desc {
  font-size: 19px;
  color: $text-secondary;
  line-height: 1.6;
  margin-bottom: $space-8;
  max-width: 480px;
  font-weight: 400;
}

.hero-actions {
  display: flex;
  gap: $space-4;

  .hero-secondary {
    background: transparent;
    border: 1px solid $text-primary;
    color: $text-primary;
    padding: 14px 32px;
    border-radius: $radius-full;
    font-weight: 500;

    &:hover {
      background: $text-primary;
      color: $color-apple-white;
    }
  }
}

.hero-visual {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $space-8;
  animation: fadeInUp 1s cubic-bezier(0.4, 0, 0.2, 1) 0.15s forwards;
  opacity: 0;
}

.hero-glow {
  position: absolute;
  width: 560px;
  height: 560px;
  background: radial-gradient(circle, rgba(0, 0, 0, 0.04) 0%, transparent 70%);
  border-radius: 50%;
}

.hero-product {
  position: relative;
  width: 460px;
  height: 460px;
  border-radius: $radius-xl;
  overflow: hidden;
  box-shadow: $shadow-xl;
  transform: perspective(1200px) rotateY(-14deg) rotateX(6deg) rotateZ(-2deg);
  transition: transform 0.7s cubic-bezier(0.22, 1, 0.36, 1);

  &:hover {
    transform: perspective(1200px) rotateY(-8deg) rotateX(3deg) rotateZ(0deg) scale(1.02);
  }

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }
}

// Categories Section
.categories-section {
  margin-bottom: $space-16;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-5;
}

.category-card {
  background: $bg-surface;
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  padding: $space-8 $space-6;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-4;
  cursor: pointer;
  transition: all $transition-base;

  &:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-md;
    border-color: $border-color;
  }
}

.category-icon {
  width: 64px;
  height: 64px;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $color-apple-gray;
  color: $text-primary;
  transition: transform $transition-bounce;

  .category-card:hover & {
    transform: scale(1.08);
  }
}

.category-name {
  font-size: 15px;
  font-weight: 600;
  color: $text-primary;
  letter-spacing: -0.01em;
}

// Products Section
.products-section {
  .container {
    max-width: $container-max-width;
    margin: 0 auto;
    padding: 0 $container-padding;
  }
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-8;

  .section-title {
    margin-bottom: 0;
  }
}

.view-all {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: 15px;
  font-weight: 500;
  color: $color-apple-blue;
  transition: gap $transition-fast;

  &:hover {
    gap: $space-3;
  }
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-6;
}

.product-card {
  background: $bg-surface;
  border-radius: $radius-xl;
  overflow: hidden;
  border: 1px solid $border-light;
  cursor: pointer;
  transition: all $transition-base;

  &:hover {
    transform: translateY(-6px);
    box-shadow: $shadow-lg;

    .product-image {
      transform: scale(1.05);
    }
  }
}

.product-image-wrapper {
  position: relative;
  aspect-ratio: 1 / 1;
  overflow: hidden;
  background: $color-apple-gray;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform $transition-slow;

  &.placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    color: $text-secondary;
    font-size: 14px;
  }
}

.product-info {
  padding: $space-6;
}

.product-name {
  font-size: 17px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $space-2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.product-desc {
  font-size: 14px;
  color: $text-secondary;
  margin-bottom: $space-4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.product-price {
  font-size: 18px;
  font-weight: 600;
  color: $color-price;

  .currency {
    font-size: 13px;
    font-weight: 600;
    margin-right: 2px;
  }
}

.product-sales {
  font-size: 12px;
  color: $text-secondary;
}

@media (max-width: 1024px) {
  .hero-section {
    grid-template-columns: 1fr;
    text-align: center;
    min-height: auto;
    padding: $space-12 0;
  }

  .hero-content {
    padding: $space-10 $space-6;
    max-width: none;
    order: 2;
  }

  .hero-actions {
    justify-content: center;
  }

  .hero-visual {
    order: 1;
    min-height: 360px;
    padding-top: $space-10;
  }

  .hero-product {
    width: 320px;
    height: 320px;
  }

  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $space-4;
  }

  .hero-product {
    width: 260px;
    height: 260px;
  }

  .hero-actions {
    flex-direction: column;
  }
}
</style>
