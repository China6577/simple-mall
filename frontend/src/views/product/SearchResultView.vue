<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import productApi from '@/api/product'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const products = ref([])
const loading = ref(false)
const total = ref(0)
const keyword = ref('')

const query = ref({
  page: 1,
  page_size: 12,
  keyword: ''
})

async function loadProducts() {
  loading.value = true
  try {
    const res = await productApi.getProducts({ ...query.value })
    products.value = res.results || []
    total.value = res.total || 0
  } catch (error) {
    console.error(error)
    products.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

function onPageChange(page) {
  query.value.page = page
  router.push({ query: { keyword: query.value.keyword, page } })
}

function goToDetail(id) {
  router.push(`/products/${id}`)
}

watch(
  () => route.query,
  () => {
    query.value.keyword = route.query.keyword || ''
    keyword.value = query.value.keyword
    query.value.page = Number(route.query.page) || 1
    loadProducts()
  },
  { immediate: true }
)

onMounted(loadProducts)
</script>

<template>
  <div class="search-result-view">
    <div class="container">
      <div class="search-header">
        <h1 class="page-title">
          "{{ keyword }}"
          <span class="result-count">共 {{ total }} 件商品</span>
        </h1>
      </div>

      <Loading v-if="loading" />
      <EmptyState v-else-if="products.length === 0" description="未找到相关商品" />

      <div v-else class="result-body">
        <div class="product-grid">
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

        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="query.page"
            :page-size="query.page_size"
            :total="total"
            layout="prev, pager, next"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.search-result-view {
  padding: $space-12 0 $space-20;
  background: $bg-body;
}

.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 $space-6;
}

.search-header {
  margin-bottom: $space-10;
  padding-bottom: $space-6;
  border-bottom: 1px solid $border-light;
  animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.page-title {
  font-family: $font-display;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: $text-primary;
  line-height: 1.2;

  .result-count {
    font-family: $font-body;
    font-size: 16px;
    color: $text-secondary;
    font-weight: 500;
    margin-left: $space-3;
  }
}

.result-body {
  animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-6;
}

.product-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  overflow: hidden;
  border: 1px solid $border-light;
  box-shadow: $shadow-sm;
  cursor: pointer;
  transition: transform $transition-base, box-shadow $transition-base;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;

  &:nth-child(1) { animation-delay: 0.05s; }
  &:nth-child(2) { animation-delay: 0.1s; }
  &:nth-child(3) { animation-delay: 0.15s; }
  &:nth-child(4) { animation-delay: 0.2s; }
  &:nth-child(5) { animation-delay: 0.25s; }
  &:nth-child(6) { animation-delay: 0.3s; }
  &:nth-child(7) { animation-delay: 0.35s; }
  &:nth-child(8) { animation-delay: 0.4s; }
  &:nth-child(9) { animation-delay: 0.45s; }
  &:nth-child(10) { animation-delay: 0.5s; }
  &:nth-child(11) { animation-delay: 0.55s; }
  &:nth-child(12) { animation-delay: 0.6s; }

  &:hover {
    transform: translateY(-12px);
    box-shadow: $shadow-lg;

    .product-image {
      transform: scale(1.06);
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
  margin-bottom: $space-5;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.5;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.product-price {
  font-size: 21px;
  font-weight: 700;
  color: $text-primary;
  letter-spacing: -0.02em;

  .currency {
    font-size: 14px;
    font-weight: 600;
    margin-right: 2px;
  }
}

.product-sales {
  font-size: 13px;
  color: $text-secondary;
}

.pagination-wrapper {
  margin-top: $space-12;
  display: flex;
  justify-content: center;
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
  .page-title {
    font-size: 32px;
  }

  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .search-header {
    margin-bottom: $space-8;
  }

  .page-title {
    font-size: 26px;

    .result-count {
      display: block;
      margin-left: 0;
      margin-top: $space-2;
      font-size: 14px;
    }
  }

  .product-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $space-5;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 $space-4;
  }

  .page-title {
    font-size: 22px;
  }

  .product-grid {
    grid-template-columns: 1fr;
  }

  .product-info {
    padding: $space-5;
  }
}
</style>
