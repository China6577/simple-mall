<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import productApi from '@/api/product'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()

const products = ref([])
const categories = ref([])
const brands = ref([])
const loading = ref(false)
const total = ref(0)

const query = ref({
  page: 1,
  page_size: 12,
  category: '',
  brand: '',
  keyword: '',
  ordering: '-created_at'
})

function initQueryFromRoute() {
  query.value.page = Number(route.query.page) || 1
  query.value.category = route.query.category || ''
  query.value.brand = route.query.brand || ''
  query.value.keyword = route.query.keyword || ''
  query.value.ordering = route.query.ordering || '-created_at'
}

async function loadCategories() {
  try {
    const res = await productApi.getCategories()
    categories.value = res || []
  } catch (error) {
    console.error(error)
  }
}

async function loadBrands() {
  try {
    const res = await productApi.getBrands()
    brands.value = res || []
  } catch (error) {
    console.error(error)
  }
}

async function loadProducts() {
  loading.value = true
  try {
    const params = { ...query.value }
    Object.keys(params).forEach((key) => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    const res = await productApi.getProducts(params)
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

function onSearch() {
  query.value.page = 1
  router.push({ query: { ...query.value } })
}

function onPageChange(page) {
  query.value.page = page
  router.push({ query: { ...query.value } })
}

function goToDetail(id) {
  router.push(`/products/${id}`)
}

watch(
  () => route.query,
  () => {
    initQueryFromRoute()
    loadProducts()
  },
  { immediate: true }
)

onMounted(() => {
  loadCategories()
  loadBrands()
})
</script>

<template>
  <div class="product-list-view">
    <div class="container">
      <!-- Page Header -->
      <div class="page-header">
        <h1 class="page-title">全部商品</h1>
        <p class="page-subtitle">精心挑选，品质之选</p>
      </div>

      <!-- Filter Bar -->
      <div class="filter-bar">
        <div class="filter-group">
          <div class="search-input">
            <el-input
              v-model="query.keyword"
              placeholder="搜索商品"
              clearable
              @keyup.enter="onSearch"
            >
              <template #suffix>
                <el-button class="search-btn" @click="onSearch">
                  <el-icon><Search /></el-icon>
                </el-button>
              </template>
            </el-input>
          </div>

          <el-select v-model="query.category" placeholder="全部分类" clearable @change="onSearch">
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="String(cat.id)"
            />
          </el-select>

          <el-select v-model="query.brand" placeholder="全部品牌" clearable @change="onSearch">
            <el-option
              v-for="brand in brands"
              :key="brand.id"
              :label="brand.name"
              :value="String(brand.id)"
            />
          </el-select>
        </div>

        <div class="sort-group">
          <div class="sort-options">
            <button
              v-for="opt in [
                { label: '最新上架', value: '-created_at' },
                { label: '最早上架', value: 'created_at' },
                { label: '名称升序', value: 'name' },
                { label: '名称降序', value: '-name' }
              ]"
              :key="opt.value"
              class="sort-btn"
              :class="{ active: query.ordering === opt.value }"
              @click="query.ordering = opt.value; onSearch()"
            >
              {{ opt.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Results Count -->
      <div v-if="!loading && products.length > 0" class="results-count">
        共 <strong>{{ total }}</strong> 件商品
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
.product-list-view {
  padding: $space-12 0 $space-20;
  background: $bg-body;
}

.container {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 $space-6;
}

.page-header {
  text-align: center;
  margin-bottom: $space-12;
  animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) both;
}

.page-title {
  font-family: $font-display;
  font-size: 56px;
  font-weight: 700;
  letter-spacing: -0.04em;
  color: $text-primary;
  margin-bottom: $space-4;
}

.page-subtitle {
  font-size: 18px;
  color: $text-secondary;
  font-weight: 400;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-6;
  margin-bottom: $space-10;
  padding: $space-6 $space-8;
  background: rgba($color-apple-white, 0.72);
  backdrop-filter: blur(20px);
  border: 1px solid $border-light;
  border-radius: $radius-xl;
  box-shadow: $shadow-sm;
  flex-wrap: wrap;
  animation: fadeInUp 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.1s both;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: $space-6;
  flex-wrap: wrap;
}

.search-input {
  width: 300px;
  margin-right: $space-2;
}

.filter-group .el-select {
  width: 160px;
}

:deep(.el-input__wrapper) {
  background: $color-apple-gray;
  border-radius: $radius-full;
  box-shadow: none;
  border: 1px solid transparent;
  padding-left: $space-5;
  padding-right: $space-5;
  height: 48px;
  transition: all $transition-base;
}

:deep(.el-input__wrapper.is-focus) {
  background: $color-apple-white;
  border-color: $color-apple-blue;
  box-shadow: 0 0 0 4px rgba($color-apple-blue, 0.15);
}

:deep(.el-input__inner) {
  color: $text-primary;
  font-size: 15px;
}

:deep(.el-input .el-input__clear) {
  color: $text-secondary;
}

:deep(.el-input__suffix-inner) {
  display: flex;
  align-items: center;
  gap: $space-1;
}

:deep(.el-input__suffix) {
  right: 6px;
}

.search-btn {
  height: 32px;
  width: 32px;
  border-radius: $radius-full;
  background: $color-apple-black;
  color: $color-apple-white;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition: transform $transition-base, background $transition-base;

  &:hover {
    background: #1d1d1f;
    transform: scale(1.05);
  }

  .el-icon {
    font-size: 14px;
  }
}

:deep(.el-select .el-input__wrapper) {
  background: $color-apple-gray;
  border-radius: $radius-full;
}

.search-input :deep(.el-input__wrapper) {
  padding-right: 6px;
}

.sort-group {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.sort-label {
  font-size: 14px;
  color: $text-secondary;
  font-weight: 500;
}

.sort-options {
  display: flex;
  gap: $space-2;
  flex-wrap: wrap;
}

.sort-btn {
  padding: 8px 16px;
  border-radius: $radius-full;
  border: 1px solid transparent;
  background: transparent;
  color: $text-secondary;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    background: $color-apple-gray;
    color: $text-primary;
  }

  &.active {
    background: $color-apple-black;
    color: $color-apple-white;
  }
}

.results-count {
  font-size: 15px;
  color: $text-secondary;
  margin-bottom: $space-8;
  animation: fadeInUp 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.15s both;

  strong {
    color: $text-primary;
    font-weight: 600;
  }
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
    font-size: 44px;
  }

  .product-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .filter-bar {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-group {
    width: 100%;
  }

  .search-input,
  .filter-group .el-select {
    flex: 1;
    min-width: 140px;
  }
}

@media (max-width: 768px) {
  .page-header {
    margin-bottom: $space-10;
  }

  .page-title {
    font-size: 36px;
  }

  .page-subtitle {
    font-size: 16px;
  }

  .product-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: $space-5;
  }

  .search-input,
  .filter-group .el-select {
    width: 100%;
  }

  .sort-group {
    width: 100%;
    justify-content: space-between;
  }

  .sort-options {
    flex-wrap: wrap;
  }
}

@media (max-width: 480px) {
  .container {
    padding: 0 $space-4;
  }

  .page-title {
    font-size: 28px;
  }

  .page-subtitle {
    font-size: 15px;
  }

  .filter-bar {
    padding: $space-5;
  }

  .product-grid {
    grid-template-columns: 1fr;
  }

  .product-info {
    padding: $space-5;
  }
}
</style>
