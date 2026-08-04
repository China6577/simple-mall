<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import couponApi from '@/api/coupon'
import Loading from '@/components/Loading.vue'

const coupons = ref([])
const myCoupons = ref([])
const loading = ref(false)
const activeTab = ref('center')
const localClaimedIds = ref(new Set())

async function loadCoupons() {
  const res = await couponApi.getCoupons()
  coupons.value = res.results || []
}

async function loadMyCoupons() {
  const res = await couponApi.getMyCoupons()
  myCoupons.value = res.results || []
}

async function loadAll(showLoading = true) {
  if (showLoading) loading.value = true
  try {
    await Promise.all([loadCoupons(), loadMyCoupons()])
  } catch (err) {
    ElMessage.error(err.message || '加载优惠券失败')
    console.error(err)
  } finally {
    if (showLoading) loading.value = false
  }
}

async function claim(coupon) {
  try {
    await couponApi.claimCoupon(coupon.id)
    ElMessage.success('领取成功')
    coupon.remaining_quantity -= 1
    localClaimedIds.value = new Set([...localClaimedIds.value, coupon.id])
    await loadMyCoupons()
  } catch (err) {
    // 全局请求拦截器已显示业务错误提示，这里不再重复弹窗
    console.error('Claim coupon failed:', err)
  }
}

function formatValue(coupon) {
  if (coupon.type === 'fixed_amount') {
    return `¥${Number(coupon.value).toFixed(0)}`
  }
  if (coupon.type === 'percentage') {
    return `${(coupon.value * 10).toFixed(1)}折`
  }
  return coupon.value
}

function formatCondition(coupon) {
  if (coupon.min_order_amount > 0) {
    return `满¥${Number(coupon.min_order_amount).toFixed(2)}可用`
  }
  return '无门槛'
}

function formatTime(time) {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

function onTabChange(tab) {
  activeTab.value = tab
  loadAll(false)
}

const claimedCouponIds = computed(() => {
  const ids = new Set(myCoupons.value.map((uc) => uc.coupon.id))
  localClaimedIds.value.forEach((id) => ids.add(id))
  return ids
})

// 无门槛优惠券优先显示
const sortedCoupons = computed(() =>
  [...coupons.value].sort((a, b) => Number(a.min_order_amount) - Number(b.min_order_amount))
)
const sortedMyCoupons = computed(() =>
  [...myCoupons.value].sort(
    (a, b) => Number(a.coupon.min_order_amount) - Number(b.coupon.min_order_amount)
  )
)

onMounted(() => {
  loadAll()
})
</script>

<template>
  <div class="coupon-center-view">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">优惠券中心</h1>
        <p class="page-subtitle">领取优惠券，享受更多购物优惠</p>
      </div>

      <div class="tabs">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'center' }"
          @click="onTabChange('center')"
        >
          领券中心
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'mine' }"
          @click="onTabChange('mine')"
        >
          我的优惠券
        </button>
      </div>

      <Loading v-if="loading" />

      <div v-else-if="activeTab === 'center'" class="coupon-list">
        <div
          v-for="(coupon, index) in sortedCoupons"
          :key="coupon.id"
          class="coupon-card"
          :class="{ disabled: !coupon.is_claimable }"
          :style="{ animationDelay: `${index * 0.05}s` }"
        >
          <div class="coupon-left">
            <div class="coupon-value">{{ formatValue(coupon) }}</div>
            <div class="coupon-condition">{{ formatCondition(coupon) }}</div>
            <div class="coupon-notch top"></div>
            <div class="coupon-notch bottom"></div>
          </div>
          <div class="coupon-right">
            <div class="coupon-header">
              <div class="coupon-name">{{ coupon.name }}</div>
              <div class="coupon-stock">剩余 {{ coupon.remaining_quantity }} 张</div>
            </div>
            <div v-if="coupon.description" class="coupon-desc">{{ coupon.description }}</div>
            <div class="coupon-time">
              <el-icon><Clock /></el-icon>
              {{ formatTime(coupon.start_time) }} ~ {{ formatTime(coupon.end_time) }}
            </div>
            <el-button
              type="primary"
              size="small"
              :disabled="!coupon.is_claimable || claimedCouponIds.has(coupon.id)"
              class="claim-btn"
              @click="claim(coupon)"
            >
              {{ claimedCouponIds.has(coupon.id) ? '已领取' : coupon.is_claimable ? '立即领取' : '已领完' }}
            </el-button>
          </div>
        </div>

        <el-empty v-if="coupons.length === 0" description="暂无可领取优惠券" />
      </div>

      <div v-else class="coupon-list">
        <div
          v-for="(uc, index) in sortedMyCoupons"
          :key="uc.id"
          class="coupon-card"
          :class="uc.status"
          :style="{ animationDelay: `${index * 0.05}s` }"
        >
          <div class="coupon-left">
            <div class="coupon-value">{{ formatValue(uc.coupon) }}</div>
            <div class="coupon-condition">{{ formatCondition(uc.coupon) }}</div>
            <div class="coupon-notch top"></div>
            <div class="coupon-notch bottom"></div>
          </div>
          <div class="coupon-right">
            <div class="coupon-header">
              <div class="coupon-name">{{ uc.coupon.name }}</div>
              <span
                class="status-badge"
                :class="uc.status"
              >
                {{ uc.status_display }}
              </span>
            </div>
            <div v-if="uc.coupon.description" class="coupon-desc">{{ uc.coupon.description }}</div>
            <div class="coupon-time">
              <el-icon><Clock /></el-icon>
              领取时间：{{ formatTime(uc.claimed_at) }}
            </div>
          </div>
        </div>

        <el-empty v-if="myCoupons.length === 0" description="暂无优惠券" />
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.coupon-center-view {
  padding: $space-10 0 $space-16;
  background: $color-apple-gray;
  min-height: calc(100vh - 72px);
}

.page-header {
  margin-bottom: $space-8;
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.page-title {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: $space-2;
  color: $text-primary;
}

.page-subtitle {
  font-size: 15px;
  color: $text-secondary;
}

.tabs {
  display: flex;
  gap: $space-1;
  margin-bottom: $space-8;
  padding: 4px;
  background: rgba(0, 0, 0, 0.04);
  border-radius: $radius-full;
  width: fit-content;
  animation: fadeInUp 0.5s 0.05s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.tab-btn {
  padding: 10px 24px;
  border-radius: $radius-full;
  border: none;
  background: transparent;
  color: $text-secondary;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all $transition-fast;

  &:hover {
    color: $text-primary;
  }

  &.active {
    background: $color-apple-white;
    color: $text-primary;
    box-shadow: $shadow-sm;
  }
}

.coupon-list {
  display: flex;
  flex-direction: column;
  gap: $space-4;
}

.coupon-card {
  display: flex;
  background: $color-apple-white;
  border-radius: $radius-xl;
  overflow: hidden;
  border: none;
  box-shadow: $shadow-sm;
  transition: all $transition-base;
  animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;

  &:hover {
    box-shadow: $shadow-md;
    transform: translateY(-2px);
  }

  &.disabled,
  &.used,
  &.expired {
    opacity: 0.6;
    filter: grayscale(0.5);

    &:hover {
      transform: none;
      box-shadow: $shadow-sm;
    }
  }
}

.coupon-left {
  position: relative;
  width: 180px;
  background: $color-apple-gray;
  color: $text-primary;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $space-6;
  flex-shrink: 0;
  border-right: 1px dashed $color-apple-border;

  .coupon-value {
    font-size: 34px;
    font-weight: 700;
    color: $color-apple-blue;
    letter-spacing: -0.03em;
  }

  .coupon-condition {
    font-size: 13px;
    margin-top: $space-2;
    color: $text-secondary;
    font-weight: 500;
  }
}

.coupon-notch {
  position: absolute;
  right: -10px;
  width: 20px;
  height: 20px;
  background: $color-apple-gray;
  border-radius: 50%;

  &.top {
    top: -10px;
  }

  &.bottom {
    bottom: -10px;
  }
}

.coupon-right {
  flex: 1;
  padding: $space-6 $space-8;
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.coupon-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.coupon-name {
  font-size: 18px;
  font-weight: 700;
  color: $text-primary;
  letter-spacing: -0.02em;
}

.coupon-stock {
  font-size: 13px;
  color: $text-secondary;
  font-weight: 500;
}

.coupon-desc {
  font-size: 14px;
  color: $text-secondary;
  line-height: 1.6;
}

.coupon-time {
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: 13px;
  color: $text-tertiary;
  margin-top: auto;
  padding-top: $space-3;

  .el-icon {
    font-size: 14px;
  }
}

.claim-btn {
  align-self: flex-start;
  margin-top: $space-3;
  border-radius: $radius-full;
  padding: 9px 22px;
  font-weight: 600;
  font-size: 13px;
  background: $color-apple-blue;
  border: none;
  transition: all $transition-base;

  &:hover:not(:disabled) {
    background: $color-apple-blue-light;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0, 113, 227, 0.22);
  }

  &:disabled,
  &:deep(.is-disabled) {
    background: $color-apple-gray !important;
    color: $text-secondary !important;
    border-color: transparent !important;
    opacity: 1;
  }
}

.status-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: $radius-full;

  &.unused {
    color: $color-success;
    background: rgba(52, 199, 89, 0.1);
  }

  &.used,
  &.expired {
    color: $text-secondary;
    background: $color-apple-gray;
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .coupon-center-view {
    padding: $space-6 0 $space-10;
  }

  .page-title {
    font-size: 28px;
  }

  .tabs {
    width: 100%;
  }

  .tab-btn {
    flex: 1;
    text-align: center;
    padding: 10px 16px;
  }

  .coupon-card {
    flex-direction: column;
    border-radius: $radius-lg;
  }

  .coupon-left {
    width: 100%;
    padding: $space-5;
    border-right: none;
    border-bottom: 1px dashed $color-apple-border;
    flex-direction: row;
    justify-content: space-between;
    align-items: center;

    .coupon-value {
      font-size: 28px;
    }

    .coupon-condition {
      margin-top: 0;
    }
  }

  .coupon-notch {
    display: none;
  }

  .coupon-right {
    padding: $space-5;
  }

  .claim-btn {
    width: 100%;
    align-self: stretch;
  }
}
</style>
