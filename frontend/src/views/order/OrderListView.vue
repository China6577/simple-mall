<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import orderApi from '@/api/order'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const router = useRouter()
const orders = ref([])
const loading = ref(false)
const pagination = ref({
  total: 0,
  page: 1,
  page_size: 10
})

const statusMap = {
  pending_payment: '待支付',
  paid: '已支付',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消'
}

const statusConfig = {
  pending_payment: { color: '#f59e0b', bg: '#fffbeb' },
  paid: { color: '#2563eb', bg: '#eff6ff' },
  shipped: { color: '#7c3aed', bg: '#f5f3ff' },
  completed: { color: '#16a34a', bg: '#f0fdf4' },
  cancelled: { color: '#64748b', bg: '#f8fafc' }
}

async function loadOrders() {
  loading.value = true
  try {
    const data = await orderApi.getOrders({
      page: pagination.value.page,
      page_size: pagination.value.page_size
    })
    orders.value = data.results || []
    pagination.value.total = data.total || 0
  } catch (error) {
    console.error(error)
    orders.value = []
  } finally {
    loading.value = false
  }
}

function onPageChange(page) {
  pagination.value.page = page
  loadOrders()
}

function viewDetail(orderNo) {
  router.push(`/orders/${orderNo}`)
}

async function payOrder(order, event) {
  event.stopPropagation()
  try {
    await orderApi.payOrder(order.order_no)
    ElMessage.success('支付成功')
    await loadOrders()
  } catch (error) {
    console.error(error)
  }
}

async function cancelOrder(order, event) {
  event.stopPropagation()
  try {
    await orderApi.cancelOrder(order.order_no)
    ElMessage.success('订单已取消')
    await loadOrders()
  } catch (error) {
    console.error(error)
  }
}

async function deleteOrder(order, event) {
  event.stopPropagation()
  try {
    await orderApi.deleteOrder(order.order_no)
    ElMessage.success('订单已删除')
    await loadOrders()
  } catch (error) {
    console.error(error)
  }
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}

function formatTime(time) {
  if (!time) return '-'
  return new Date(time).toLocaleString('zh-CN')
}

onMounted(loadOrders)
</script>

<template>
  <div class="order-list-view">
    <div class="container">
      <div class="page-header fade-in-up">
        <h1 class="page-title">我的订单</h1>
        <p class="page-subtitle">查看和管理您的所有订单</p>
      </div>

      <Loading v-if="loading" />
      <EmptyState
        v-else-if="orders.length === 0"
        description="暂无订单"
        action-text="去商店逛逛"
        action-link="/products"
      />

      <div v-else class="order-list">
        <div
          v-for="(order, index) in orders"
          :key="order.order_no"
          class="order-card fade-in-up"
          :style="{ animationDelay: `${80 + index * 60}ms` }"
          @click="viewDetail(order.order_no)"
        >
          <div class="order-header">
            <div class="order-meta">
              <span class="order-no">订单号：{{ order.order_no }}</span>
              <span class="order-time">{{ formatTime(order.created_at) }}</span>
            </div>
            <span class="order-status" :style="{ color: statusConfig[order.status]?.color, background: statusConfig[order.status]?.bg }">
              {{ statusMap[order.status] || order.status }}
            </span>
          </div>

          <div class="order-body">
            <div class="order-preview">
              <img
                v-if="order.items?.[0]?.main_image"
                :src="order.items[0].main_image"
                class="preview-image"
                alt="商品图片"
              />
              <div class="preview-info">
                <p class="preview-name">{{ order.items?.[0]?.spu_name || '商品' }}</p>
                <p v-if="order.item_count > 1" class="preview-more">等 {{ order.item_count }} 件商品</p>
              </div>
            </div>
            <div class="order-amount">
              <span class="label">应付总额</span>
              <span class="price">¥{{ formatPrice(order.payable_amount) }}</span>
            </div>
          </div>

          <div class="order-actions">
            <el-button
              v-if="order.status === 'pending_payment'"
              type="primary"
              size="small"
              class="action-btn primary"
              @click="(e) => payOrder(order, e)"
            >
              立即支付
            </el-button>
            <el-button
              v-if="order.status === 'pending_payment'"
              size="small"
              plain
              class="action-btn secondary"
              @click="(e) => cancelOrder(order, e)"
            >
              取消订单
            </el-button>
            <el-button
              v-if="order.status === 'cancelled' || order.status === 'completed'"
              size="small"
              type="danger"
              plain
              class="action-btn danger"
              @click="(e) => deleteOrder(order, e)"
            >
              删除记录
            </el-button>
            <el-button size="small" plain class="action-btn secondary" @click="(e) => viewDetail(order.order_no) && e.stopPropagation()">
              查看详情
            </el-button>
          </div>
        </div>

        <div class="pagination-row fade-in-up" style="animation-delay: 200ms">
          <el-pagination
            v-model:current-page="pagination.page"
            :page-size="pagination.page_size"
            :total="pagination.total"
            layout="prev, pager, next"
            @current-change="onPageChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.order-list-view {
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

.order-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-6 $space-8;
  margin-bottom: $space-5;
  border: 1px solid $color-apple-border-light;
  box-shadow: $shadow-md;
  cursor: pointer;
  transition: all $transition-base;

  &:hover {
    box-shadow: $shadow-lg;
    transform: translateY(-3px);
  }
}

.order-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-5;
  padding-bottom: $space-4;
  border-bottom: 1px solid $border-light;
}

.order-meta {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}

.order-no {
  color: $text-primary;
  font-size: 14px;
  font-weight: 700;
}

.order-time {
  color: $text-secondary;
  font-size: 13px;
}

.order-status {
  font-size: 13px !important;
  font-weight: 700 !important;
  padding: 6px 16px !important;
  border-radius: $radius-full !important;
  transition: all $transition-fast;
}

// Override script-level saturated status colors with refined Apple palette
.order-status[style*="#f59e0b"] {
  color: $text-primary !important;
  background: $color-apple-gray !important;
}

.order-status[style*="#2563eb"] {
  color: $color-apple-blue !important;
  background: $color-apple-blue-soft !important;
}

.order-status[style*="#7c3aed"] {
  color: $color-info !important;
  background: rgba(94, 92, 230, 0.08) !important;
}

.order-status[style*="#16a34a"] {
  color: $color-success !important;
  background: rgba(52, 199, 89, 0.08) !important;
}

.order-status[style*="#64748b"] {
  color: $text-secondary !important;
  background: $color-apple-gray !important;
}

.order-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: $space-5;
}

.order-preview {
  display: flex;
  align-items: center;
  gap: $space-5;
}

.preview-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: $radius-lg;
  background: $color-apple-gray;
}

.preview-name {
  font-size: 16px;
  font-weight: 600;
  color: $text-primary;
  margin-bottom: $space-1;
  letter-spacing: -0.01em;
}

.preview-more {
  font-size: 14px;
  color: $text-secondary;
}

.order-amount {
  text-align: right;

  .label {
    display: block;
    font-size: 13px;
    color: $text-secondary;
    margin-bottom: $space-1;
  }

  .price {
    font-size: 24px;
    font-weight: 800;
    color: $text-primary;
    letter-spacing: -0.03em;
  }
}

.order-actions {
  display: flex;
  justify-content: flex-end;
  gap: $space-3;
}

.action-btn {
  border-radius: $radius-full;
  font-weight: 600;
  transition: transform $transition-fast, box-shadow $transition-fast;

  &:hover {
    transform: scale(1.04);
  }

  &:active {
    transform: scale(0.98);
  }

  &.primary {
    background: $color-apple-black;
    border-color: $color-apple-black;
    color: $color-apple-white;

    &:hover {
      background: $color-apple-black;
      border-color: $color-apple-black;
    }
  }

  &.secondary {
    background: $color-apple-white;
    border-color: $color-apple-border;
    color: $text-primary;

    &:hover {
      border-color: $text-primary;
      color: $text-primary;
    }
  }

  &.danger {
    background: $color-apple-white;
    border-color: $color-apple-border;
    color: $color-danger;

    &:hover {
      border-color: $color-danger;
      background: rgba(255, 59, 48, 0.04);
    }
  }
}

.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: $space-8;
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

@media (max-width: 768px) {
  .page-title {
    font-size: 32px;
  }

  .order-card {
    padding: $space-5 $space-6;
  }

  .order-body {
    flex-direction: column;
    align-items: flex-start;
    gap: $space-4;
  }

  .order-amount {
    text-align: left;
  }

  .order-actions {
    flex-wrap: wrap;
  }
}
</style>
