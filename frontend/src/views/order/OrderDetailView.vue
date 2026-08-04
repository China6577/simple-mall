<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Picture } from '@element-plus/icons-vue'
import orderApi from '@/api/order'
import Loading from '@/components/Loading.vue'

const route = useRoute()
const router = useRouter()

const order = ref(null)
const loading = ref(false)

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

const statusSteps = {
  pending_payment: 0,
  paid: 1,
  shipped: 2,
  completed: 3,
  cancelled: 0
}

const currentStep = computed(() => {
  return statusSteps[order.value?.status] ?? 0
})

async function loadOrder() {
  const orderNo = route.params.orderNo
  if (!orderNo) return

  loading.value = true
  try {
    order.value = await orderApi.getOrderDetail(orderNo)
  } catch (error) {
    console.error(error)
    order.value = null
  } finally {
    loading.value = false
  }
}

async function payOrder() {
  try {
    await orderApi.payOrder(order.value.order_no)
    ElMessage.success('支付成功')
    await loadOrder()
  } catch (error) {
    console.error(error)
  }
}

async function cancelOrder() {
  try {
    await orderApi.cancelOrder(order.value.order_no)
    ElMessage.success('订单已取消')
    await loadOrder()
  } catch (error) {
    console.error(error)
  }
}

async function confirmReceive() {
  try {
    await orderApi.confirmOrder(order.value.order_no)
    ElMessage.success('确认收货成功')
    await loadOrder()
  } catch (error) {
    console.error(error)
  }
}

async function deleteOrder() {
  try {
    await orderApi.deleteOrder(order.value.order_no)
    ElMessage.success('订单已删除')
    router.push('/orders')
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

onMounted(loadOrder)
</script>

<template>
  <div class="order-detail-view">
    <div class="container">
      <div class="page-header fade-in-up">
        <h1 class="page-title">订单详情</h1>
        <el-button link class="back-btn" @click="router.push('/orders')">
          <el-icon><ArrowLeft /></el-icon>
          返回订单列表
        </el-button>
      </div>

      <Loading v-if="loading" />
      <div v-else-if="!order" class="empty-state">订单不存在</div>

      <div v-else class="detail-layout">
        <div class="detail-main">
          <!-- Status Steps -->
          <div v-if="order.status !== 'cancelled'" class="detail-card status-section fade-in-up" style="animation-delay: 80ms">
            <el-steps :active="currentStep" finish-status="success" align-center class="order-steps">
              <el-step title="提交订单" />
              <el-step title="支付成功" />
              <el-step title="商家发货" />
              <el-step title="确认收货" />
            </el-steps>
          </div>

          <!-- Order Status -->
          <div class="detail-card fade-in-up" style="animation-delay: 120ms">
            <div class="status-header">
              <div>
                <p class="status-label">当前状态</p>
                <p class="status-value" :style="{ color: statusConfig[order.status]?.color }">
                  {{ statusMap[order.status] || order.status }}
                </p>
              </div>
              <div class="order-nums">
                <p><span>订单编号：</span>{{ order.order_no }}</p>
                <p><span>创建时间：</span>{{ formatTime(order.created_at) }}</p>
              </div>
            </div>
          </div>

          <!-- Address -->
          <div class="detail-card fade-in-up" style="animation-delay: 180ms">
            <h2 class="card-title">收货信息</h2>
            <div class="address-content">
              <p class="receiver">
                <strong>{{ order.address_snapshot.receiver }}</strong>
                <span>{{ order.address_snapshot.phone }}</span>
              </p>
              <p class="address-text">
                {{ order.address_snapshot.province }} {{ order.address_snapshot.city }}
                {{ order.address_snapshot.district }} {{ order.address_snapshot.detail }}
              </p>
            </div>
          </div>

          <!-- Remark -->
          <div v-if="order.remark" class="detail-card fade-in-up" style="animation-delay: 240ms">
            <h2 class="card-title">订单备注</h2>
            <p class="remark-text">{{ order.remark }}</p>
          </div>

          <!-- Items -->
          <div class="detail-card fade-in-up" style="animation-delay: 300ms">
            <h2 class="card-title">商品清单</h2>
            <div class="item-list">
              <div v-for="item in order.items" :key="item.id" class="item">
                <el-image
                  :src="item.main_image"
                  class="item-image"
                  fit="cover"
                  :preview-src-list="[item.main_image]"
                  hide-on-click-modal
                >
                  <template #error>
                    <div class="image-fallback">
                      <el-icon><Picture /></el-icon>
                    </div>
                  </template>
                </el-image>
                <div class="item-info">
                  <p class="item-name">{{ item.spu_name }}</p>
                  <p class="item-specs">{{ Object.values(item.specs || {}).join(' / ') }}</p>
                </div>
                <div class="item-price">¥{{ formatPrice(item.price) }}</div>
                <div class="item-quantity">x{{ item.quantity }}</div>
                <div class="item-subtotal">¥{{ formatPrice(item.subtotal) }}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Summary -->
        <div class="detail-sidebar">
          <div class="summary-card fade-in-up" style="animation-delay: 160ms">
            <h3 class="summary-title">订单金额</h3>
            <div class="summary-row">
              <span>商品总额</span>
              <span>¥{{ formatPrice(order.total_amount) }}</span>
            </div>
            <div class="summary-row">
              <span>运费</span>
              <span>¥{{ formatPrice(order.freight_amount) }}</span>
            </div>
            <div class="summary-row">
              <span>优惠</span>
              <span>-¥{{ formatPrice(order.discount_amount || 0) }}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-row total">
              <span>应付总额</span>
              <span class="payable">¥{{ formatPrice(order.payable_amount) }}</span>
            </div>
          </div>

          <div class="action-card fade-in-up" style="animation-delay: 220ms">
            <template v-if="order.status === 'pending_payment'">
              <el-button type="primary" size="large" class="action-btn primary" @click="payOrder">
                立即支付
              </el-button>
              <el-button size="large" plain class="action-btn secondary" @click="cancelOrder">
                取消订单
              </el-button>
            </template>
            <template v-else-if="order.status === 'paid'">
              <el-button type="primary" size="large" class="action-btn primary" @click="router.push('/')">
                再次购买
              </el-button>
              <el-button size="large" plain class="action-btn secondary" @click="ElMessage.info('商家暂未发货，请耐心等待')">
                查看物流
              </el-button>
            </template>
            <template v-else-if="order.status === 'shipped'">
              <el-button type="primary" size="large" class="action-btn primary" @click="confirmReceive">
                确认收货
              </el-button>
              <el-button size="large" plain class="action-btn secondary" @click="router.push('/')">
                再次购买
              </el-button>
            </template>
            <template v-else-if="order.status === 'completed'">
              <el-button type="primary" size="large" class="action-btn primary" @click="router.push('/')">
                再次购买
              </el-button>
              <el-button type="danger" size="large" plain class="action-btn danger" @click="deleteOrder">
                删除记录
              </el-button>
            </template>
            <template v-else-if="order.status === 'cancelled'">
              <el-button type="primary" size="large" class="action-btn primary" @click="router.push('/')">
                再次购买
              </el-button>
              <el-button type="danger" size="large" plain class="action-btn danger" @click="deleteOrder">
                删除记录
              </el-button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.order-detail-view {
  padding: $space-10 0 $space-20;
  background: $color-apple-gray;
  min-height: 100vh;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-8;
}

.page-title {
  font-family: $font-display;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -0.03em;
  color: $text-primary;
}

.back-btn {
  color: $text-secondary;
  font-weight: 500;
  font-size: 15px;

  &:hover {
    color: $color-apple-blue;
  }
}

.empty-state {
  text-align: center;
  padding: $space-12;
  color: $text-secondary;
  font-size: 16px;
}

.detail-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: $space-8;
  align-items: start;
}

.detail-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-8;
  margin-bottom: $space-6;
  border: 1px solid $color-apple-border-light;
  box-shadow: $shadow-md;
}

.status-section {
  padding: $space-10 $space-8;
}

.order-steps {
  :deep(.el-step__title) {
    font-size: 14px;
    font-weight: 600;
    color: $text-secondary;
  }

  :deep(.el-step__title.is-success),
  :deep(.el-step__title.is-process) {
    color: $text-primary;
  }

  :deep(.el-step__icon-inner) {
    color: $color-apple-white;
  }

  :deep(.el-step__head.is-success) {
    color: $color-success;
    border-color: $color-success;
  }

  :deep(.el-step__head.is-process) {
    color: $color-apple-blue;
    border-color: $color-apple-blue;
  }
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;

  .status-label {
    font-size: 14px;
    color: $text-secondary;
    margin-bottom: $space-2;
    font-weight: 500;
  }

  .status-value {
    font-family: $font-display;
    font-size: 28px;
    font-weight: 800;
    letter-spacing: -0.03em;
    color: $text-primary !important;
  }
}

.order-nums {
  text-align: right;

  p {
    font-size: 14px;
    color: $text-secondary;
    margin-bottom: $space-1;

    span {
      color: $text-tertiary;
    }
  }
}

.card-title {
  font-family: $font-display;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: $space-6;
  color: $text-primary;
  letter-spacing: -0.02em;
}

.address-content {
  .receiver {
    font-size: 16px;
    margin-bottom: $space-2;

    strong {
      font-weight: 700;
      color: $text-primary;
      margin-right: $space-3;
    }

    span {
      color: $text-secondary;
    }
  }

  .address-text {
    font-size: 15px;
    color: $text-secondary;
    line-height: 1.6;
  }
}

.remark-text {
  font-size: 15px;
  color: $text-secondary;
  line-height: 1.7;
  word-break: break-word;
}

.item-list {
  .item {
    display: flex;
    align-items: center;
    gap: $space-5;
    padding: $space-5 0;
    border-bottom: 1px solid $border-light;

    &:last-child {
      border-bottom: none;
    }
  }

  .item-image {
    width: 88px;
    height: 88px;
    object-fit: cover;
    border-radius: $radius-lg;
    background: $color-apple-gray;
    overflow: hidden;

    :deep(.el-image__inner) {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .image-fallback {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      background: $color-apple-gray;
      color: $text-secondary;
      font-size: 24px;
    }
  }

  .item-info {
    flex: 1;

    .item-name {
      font-size: 16px;
      font-weight: 600;
      color: $text-primary;
      margin-bottom: $space-1;
      letter-spacing: -0.01em;
    }

    .item-specs {
      font-size: 14px;
      color: $text-secondary;
    }
  }

  .item-price,
  .item-quantity,
  .item-subtotal {
    width: 100px;
    text-align: center;
    font-size: 14px;
  }

  .item-price {
    color: $text-secondary;
    font-weight: 500;
  }

  .item-quantity {
    color: $text-secondary;
  }

  .item-subtotal {
    color: $text-primary;
    font-weight: 700;
    font-size: 16px;
  }
}

.detail-sidebar {
  position: sticky;
  top: 96px;
}

.summary-card,
.action-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-8;
  border: 1px solid $color-apple-border-light;
  box-shadow: $shadow-md;
  margin-bottom: $space-6;
  display: flex;
  flex-direction: column;
  gap: $space-3;
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

  &.total {
    font-size: 16px;
    font-weight: 700;
    color: $text-primary;
    margin-bottom: 0;

    .payable {
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
  margin: $space-5 0;
}

.action-btn {
  width: 100%;
  height: 50px;
  font-size: 15px;
  font-weight: 600;
  border-radius: $radius-full;
  margin: 0;
  transition: transform $transition-fast, box-shadow $transition-fast;

  &:hover {
    transform: scale(1.02);
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
      box-shadow: $shadow-lg;
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
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 32px;
  }

  .status-header {
    flex-direction: column;
    gap: $space-4;

    .order-nums {
      text-align: left;
    }
  }

  .item {
    flex-wrap: wrap;
  }

  .item-price,
  .item-quantity,
  .item-subtotal {
    width: auto !important;
    text-align: left;
  }
}
</style>
