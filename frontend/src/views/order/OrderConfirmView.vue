<script setup>
import { ref, onMounted, computed, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { regionData } from 'element-china-area-data'
import { useCartStore } from '@/stores/cart'
import orderApi from '@/api/order'
import userApi from '@/api/user'
import couponApi from '@/api/coupon'
import Loading from '@/components/Loading.vue'
import EmptyState from '@/components/EmptyState.vue'

const route = useRoute()
const router = useRouter()
const cartStore = useCartStore()

const addresses = ref([])
const selectedAddressId = ref(null)
const addressMode = ref('existing') // 'existing' | 'new'
const addressFormRef = ref(null)
const savingAddress = ref(false)
const addressForm = reactive({
  receiver: '',
  phone: '',
  province: '',
  city: '',
  district: '',
  detail: '',
  zip_code: '',
  is_default: false
})
const phonePattern = /^1[3-9]\d{9}$/
const addressRules = {
  receiver: [{ required: true, message: '请输入收货人', trigger: [] }],
  phone: [
    { required: true, message: '请输入手机号', trigger: [] },
    { pattern: phonePattern, message: '请输入正确的手机号', trigger: [] }
  ],
  province: [{ required: true, message: '请选择省份', trigger: [] }],
  city: [{ required: true, message: '请选择城市', trigger: [] }],
  district: [{ required: true, message: '请选择区县', trigger: [] }],
  detail: [{ required: true, message: '请输入详细地址', trigger: [] }]
}

// 中国省市区数据（使用 label 作为 value，直接绑定到地址字段）
const provinces = computed(() =>
  regionData.map((province) => ({ value: province.label, label: province.label }))
)

const cities = computed(() => {
  const province = regionData.find((p) => p.label === addressForm.province)
  if (!province || !province.children) return []
  return province.children.map((city) => ({ value: city.label, label: city.label }))
})

const districts = computed(() => {
  const province = regionData.find((p) => p.label === addressForm.province)
  if (!province || !province.children) return []
  const city = province.children.find((c) => c.label === addressForm.city)
  if (!city || !city.children) return []
  return city.children.map((district) => ({ value: district.label, label: district.label }))
})

function onProvinceChange() {
  addressForm.city = ''
  addressForm.district = ''
}

function onCityChange() {
  addressForm.district = ''
}
const remark = ref('')
const loading = ref(false)
const submitting = ref(false)
const availableCoupons = ref([])
const selectedCouponIds = ref([])
const couponDiscount = ref(0)

const cartItemIds = computed(() => {
  const ids = route.query.ids
  if (!ids) return []
  return String(ids)
    .split(',')
    .map((id) => parseInt(id, 10))
    .filter((id) => !isNaN(id))
})

const selectedItems = computed(() => {
  return cartStore.items.filter((item) => cartItemIds.value.includes(item.id))
})

const totalAmount = computed(() => {
  return selectedItems.value.reduce((sum, item) => {
    return sum + Number(item.subtotal)
  }, 0)
})

const freightAmount = computed(() => 0)

const payableAmount = computed(() => {
  const amount = totalAmount.value + freightAmount.value - couponDiscount.value
  return amount > 0 ? amount : 0
})

async function loadAvailableCoupons() {
  if (cartItemIds.value.length === 0) return
  try {
    const res = await couponApi.getAvailableForCart(cartItemIds.value)
    availableCoupons.value = res.coupons || []
  } catch (error) {
    console.error(error)
    availableCoupons.value = []
  }
}

async function onCouponChange() {
  // 过滤出实际可用的券，避免不可用的券参与计算导致报错
  const usableIds = availableCoupons.value
    .filter((item) => item.usable && selectedCouponIds.value.includes(item.user_coupon.id))
    .map((item) => item.user_coupon.id)

  // 如果用户勾选了不可用券，自动从选中列表移除（禁用状态理论上不会被选中，兜底）
  if (usableIds.length !== selectedCouponIds.value.length) {
    selectedCouponIds.value = usableIds
  }

  if (usableIds.length === 0) {
    couponDiscount.value = 0
    return
  }
  try {
    const res = await couponApi.calculate({
      coupon_ids: usableIds,
      total_amount: String(totalAmount.value)
    })
    couponDiscount.value = Number(res.discount_amount || 0)
  } catch (err) {
    ElMessage.error(err.message || '优惠券计算失败')
    couponDiscount.value = 0
  }
}

async function loadAddresses() {
  try {
    const res = await userApi.getAddresses()
    // 后端地址列表启用了分页，统一取 results；兼容直接返回数组的情况
    addresses.value = Array.isArray(res) ? res : res.results || []
    const defaultAddress = addresses.value.find((addr) => addr.is_default)
    selectedAddressId.value = defaultAddress?.id || addresses.value[0]?.id || null
  } catch (error) {
    console.error(error)
    addresses.value = []
  }
}

function resetAddressForm() {
  addressForm.receiver = ''
  addressForm.phone = ''
  addressForm.province = ''
  addressForm.city = ''
  addressForm.district = ''
  addressForm.detail = ''
  addressForm.zip_code = ''
  addressForm.is_default = false
  addressFormRef.value?.clearValidate()
}

async function saveNewAddress() {
  const valid = await addressFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingAddress.value = true
  try {
    const newAddress = await userApi.createAddress(addressForm)
    await loadAddresses()
    selectedAddressId.value = newAddress.id
    addressMode.value = 'existing'
    resetAddressForm()
    ElMessage.success('地址已保存')
  } catch (error) {
    console.error(error)
  } finally {
    savingAddress.value = false
  }
}

async function submitOrder() {
  if (selectedItems.value.length === 0) {
    ElMessage.warning('没有选择商品')
    return
  }

  if (!selectedAddressId.value) {
    ElMessage.warning('请选择或填写收货地址')
    return
  }

  submitting.value = true
  try {
    const idempotencyKey = `order-${Date.now()}-${Math.random().toString(36).slice(2)}`
    const data = await orderApi.createOrder({
      cart_item_ids: cartItemIds.value,
      address_id: selectedAddressId.value,
      remark: remark.value,
      idempotency_key: idempotencyKey,
      coupon_ids: selectedCouponIds.value
    })
    ElMessage.success('订单创建成功')
    await cartStore.loadCart()
    router.push(`/orders/${data.order_no}`)
  } catch (error) {
    console.error(error)
  } finally {
    submitting.value = false
  }
}

function formatPrice(price) {
  return Number(price).toFixed(2)
}

onMounted(async () => {
  loading.value = true
  await cartStore.loadCart()
  await loadAddresses()
  await loadAvailableCoupons()
  loading.value = false
})
</script>

<template>
  <div class="order-confirm-view">
    <div class="container">
      <div class="page-header fade-in-up">
        <h1 class="page-title">确认订单</h1>
        <p class="page-subtitle">请确认订单信息并提交</p>
      </div>

      <Loading v-if="loading" />
      <EmptyState v-else-if="selectedItems.length === 0" description="没有选择商品，返回购物车重试" />

      <div v-else class="confirm-layout">
        <div class="confirm-main">
          <!-- Address -->
          <div class="confirm-card fade-in-up" style="animation-delay: 80ms">
            <h2 class="card-title">
              <span class="title-icon"><el-icon><Location /></el-icon></span>
              收货地址
            </h2>
            <el-tabs v-model="addressMode" class="address-mode">
              <el-tab-pane label="选择已有地址" name="existing">
                <div v-if="addresses.length === 0" class="empty-tip">
                  暂无收货地址，请切换到"填写新地址"添加
                </div>
                <el-radio-group v-else v-model="selectedAddressId" class="address-list">
                  <el-radio
                    v-for="addr in addresses"
                    :key="addr.id"
                    :label="addr.id"
                    border
                    class="address-card"
                  >
                    <div class="address-info">
                      <p class="receiver">
                        <strong>{{ addr.receiver }}</strong>
                        <span>{{ addr.phone }}</span>
                        <span v-if="addr.is_default" class="default-tag">默认</span>
                      </p>
                      <p class="address-text">
                        {{ addr.province }} {{ addr.city }} {{ addr.district }} {{ addr.detail }}
                      </p>
                    </div>
                  </el-radio>
                </el-radio-group>
              </el-tab-pane>

              <el-tab-pane label="填写新地址" name="new">
                <div class="new-address-form">
                  <el-form
                    ref="addressFormRef"
                    :model="addressForm"
                    :rules="addressRules"
                    label-position="top"
                  >
                    <el-row :gutter="16">
                      <el-col :span="12">
                        <el-form-item label="收货人" prop="receiver">
                          <el-input v-model="addressForm.receiver" />
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item label="手机号" prop="phone">
                          <el-input v-model="addressForm.phone" />
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-row :gutter="16">
                      <el-col :span="8">
                        <el-form-item label="省份" prop="province">
                          <el-select
                            v-model="addressForm.province"
                            placeholder="请选择省份"
                            style="width: 100%"
                            @change="onProvinceChange"
                          >
                            <el-option
                              v-for="item in provinces"
                              :key="item.value"
                              :label="item.label"
                              :value="item.value"
                            />
                          </el-select>
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="城市" prop="city">
                          <el-select
                            v-model="addressForm.city"
                            placeholder="请选择城市"
                            :disabled="!addressForm.province"
                            style="width: 100%"
                            @change="onCityChange"
                          >
                            <el-option
                              v-for="item in cities"
                              :key="item.value"
                              :label="item.label"
                              :value="item.value"
                            />
                          </el-select>
                        </el-form-item>
                      </el-col>
                      <el-col :span="8">
                        <el-form-item label="区县" prop="district">
                          <el-select
                            v-model="addressForm.district"
                            placeholder="请选择区县"
                            :disabled="!addressForm.city"
                            style="width: 100%"
                          >
                            <el-option
                              v-for="item in districts"
                              :key="item.value"
                              :label="item.label"
                              :value="item.value"
                            />
                          </el-select>
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-form-item label="详细地址" prop="detail">
                      <el-input v-model="addressForm.detail" type="textarea" :rows="2" />
                    </el-form-item>
                    <el-row :gutter="16">
                      <el-col :span="12">
                        <el-form-item label="邮编">
                          <el-input v-model="addressForm.zip_code" />
                        </el-form-item>
                      </el-col>
                      <el-col :span="12">
                        <el-form-item>
                          <el-checkbox v-model="addressForm.is_default">设为默认地址</el-checkbox>
                        </el-form-item>
                      </el-col>
                    </el-row>
                    <el-form-item>
                      <el-button type="primary" :loading="savingAddress" class="save-address-btn" @click="saveNewAddress">
                        保存并使用该地址
                      </el-button>
                    </el-form-item>
                  </el-form>
                </div>
              </el-tab-pane>
            </el-tabs>
          </div>

          <!-- Items -->
          <div class="confirm-card fade-in-up" style="animation-delay: 140ms">
            <h2 class="card-title">
              <span class="title-icon"><el-icon><Goods /></el-icon></span>
              商品清单
            </h2>
            <div class="item-list">
              <div v-for="item in selectedItems" :key="item.id" class="item">
                <img
                  :src="item.spu_main_image || item.sku?.spu?.main_image_url || ''"
                  class="item-image"
                  alt="商品图片"
                />
                <div class="item-info">
                  <p class="item-name">{{ item.spu_name }}</p>
                  <p class="item-specs">{{ Object.values(item.sku?.specs || {}).join(' / ') }}</p>
                </div>
                <div class="item-price">¥{{ formatPrice(item.sku?.price) }}</div>
                <div class="item-quantity">x{{ item.quantity }}</div>
                <div class="item-subtotal">¥{{ formatPrice(item.subtotal) }}</div>
              </div>
            </div>
          </div>

          <!-- Coupons -->
          <div class="confirm-card fade-in-up" style="animation-delay: 200ms">
            <h2 class="card-title">
              <span class="title-icon"><el-icon><Ticket /></el-icon></span>
              优惠券
            </h2>
            <div v-if="availableCoupons.length === 0" class="empty-tip">暂无优惠券</div>
            <el-checkbox-group v-else v-model="selectedCouponIds" @change="onCouponChange">
              <el-checkbox
                v-for="item in availableCoupons"
                :key="item.user_coupon.id"
                :label="item.user_coupon.id"
                border
                :disabled="!item.usable"
                class="coupon-option"
                :class="{ disabled: !item.usable }"
              >
                <span class="coupon-name">{{ item.user_coupon.coupon.name }}</span>
                <span v-if="item.usable" class="coupon-discount">-¥{{ formatPrice(item.discount_amount) }}</span>
                <span v-else class="coupon-reason">{{ item.reason }}</span>
              </el-checkbox>
            </el-checkbox-group>
          </div>

          <!-- Remark -->
          <div class="confirm-card fade-in-up" style="animation-delay: 260ms">
            <h2 class="card-title">
              <span class="title-icon"><el-icon><Edit /></el-icon></span>
              订单备注
            </h2>
            <el-input v-model="remark" placeholder="请输入备注（选填）" maxlength="255" show-word-limit type="textarea" :rows="3" />
          </div>
        </div>

        <!-- Summary Sidebar -->
        <div class="confirm-sidebar">
          <div class="summary-card fade-in-up" style="animation-delay: 180ms">
            <h3 class="summary-title">结算明细</h3>
            <div class="summary-row">
              <span>商品总额</span>
              <span>¥{{ formatPrice(totalAmount) }}</span>
            </div>
            <div class="summary-row">
              <span>运费</span>
              <span class="free">免运费</span>
            </div>
            <div class="summary-row">
              <span>优惠</span>
              <span class="discount">-¥{{ formatPrice(couponDiscount) }}</span>
            </div>
            <div class="summary-divider"></div>
            <div class="summary-row total">
              <span>应付总额</span>
              <span class="payable">¥{{ formatPrice(payableAmount) }}</span>
            </div>
            <el-button type="primary" size="large" :loading="submitting" class="submit-btn" @click="submitOrder">
              提交订单
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
.order-confirm-view {
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

.confirm-layout {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: $space-8;
  align-items: start;
}

.confirm-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-8;
  margin-bottom: $space-6;
  border: 1px solid $color-apple-border-light;
  box-shadow: $shadow-md;
}

.card-title {
  font-family: $font-display;
  font-size: 20px;
  font-weight: 700;
  margin-bottom: $space-6;
  display: flex;
  align-items: center;
  gap: $space-3;
  color: $text-primary;
  letter-spacing: -0.02em;

  .title-icon {
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: $radius-md;
    background: $color-apple-gray;
    color: $color-apple-blue;
    font-size: 18px;
  }
}

.empty-tip {
  color: $text-secondary;
  font-size: 14px;
}

.address-mode {
  margin-bottom: $space-4;
}

.new-address-form {
  :deep(.el-form-item__label) {
    padding-bottom: $space-1;
    font-weight: 600;
    color: $text-primary !important;
    opacity: 1;
  }

  :deep(.el-form-item.is-required .el-form-item__label::before) {
    color: $color-danger;
  }

  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner) {
    border-radius: $radius-md;
    box-shadow: 0 0 0 1px $color-apple-border inset;
  }
}

.save-address-btn {
  border-radius: $radius-full;
  height: 44px;
  padding: 0 $space-6;
  font-weight: 600;
  background: $color-apple-black;
  border-color: $color-apple-black;

  &:hover {
    background: $color-apple-black;
    border-color: $color-apple-black;
    transform: scale(1.02);
  }
}

.address-list {
  display: flex;
  flex-direction: column;
  gap: $space-3;
  width: 100%;

  :deep(.el-radio-group) {
    display: flex;
    flex-direction: column;
    gap: $space-3;
    width: 100%;
  }

  :deep(.el-radio) {
    margin-right: 0;
  }

  .address-card {
    width: 100%;
    height: auto;
    padding: $space-5 $space-6;
    border-radius: $radius-lg;
    border-color: $color-apple-border;
    background: $color-apple-white;
    transition: all $transition-fast;
    display: flex;
    align-items: flex-start;
    gap: $space-4;

    &:hover {
      border-color: $color-apple-blue;
      box-shadow: $shadow-sm;
    }

    &.is-checked {
      border-color: $color-apple-blue;
      background: $color-apple-blue-soft;
    }

    :deep(.el-radio__input) {
      flex-shrink: 0;
      margin-top: 2px;
    }

    :deep(.el-radio__label) {
      flex: 1;
      padding: 0;
      min-width: 0;
    }

    .address-info {
      margin-left: 0;
    }

    .receiver {
      margin-bottom: $space-2;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: $space-2;

      strong {
        margin-right: $space-1;
        font-weight: 700;
        color: $text-primary;
      }

      span {
        color: $text-secondary;
      }

      .default-tag {
        font-size: 11px;
        font-weight: 600;
        color: $color-apple-blue;
        background: rgba(0, 113, 227, 0.1);
        padding: 2px 8px;
        border-radius: $radius-full;
        line-height: 1;
      }
    }

    .address-text {
      color: $text-secondary;
      font-size: 14px;
      line-height: 1.6;
    }
  }
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

.coupon-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-3;
  padding: $space-5 $space-6;
  border-radius: $radius-lg;
  border-color: $color-apple-border;
  width: 100%;
  background: $color-apple-white;
  transition: all $transition-fast;

  &:hover {
    border-color: $color-apple-blue;
  }

  &.is-checked {
    border-color: $color-apple-blue;
    background: $color-apple-blue-soft;
  }

  .coupon-name {
    font-weight: 600;
    color: $text-primary;
  }

  .coupon-discount {
    color: $text-primary;
    font-weight: 700;
    margin-left: $space-3;
  }

  .coupon-reason {
    color: $text-secondary;
    font-size: 13px;
    margin-left: $space-3;
  }

  &.disabled {
    opacity: 0.6;
    background: $color-apple-gray;
  }
}

.confirm-sidebar {
  position: sticky;
  top: 96px;
}

.summary-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-8;
  border: 1px solid $color-apple-border-light;
  box-shadow: $shadow-md;
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

  .discount {
    color: $text-primary;
    font-weight: 700;
  }

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
  margin: $space-6 0;
}

.submit-btn {
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
  .confirm-layout {
    grid-template-columns: 1fr;
  }

  .confirm-sidebar {
    position: static;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 32px;
  }

  .confirm-card {
    padding: $space-6;
  }

  .item-list {
    .item {
      flex-wrap: wrap;
      gap: $space-4;
    }

    .item-price,
    .item-quantity,
    .item-subtotal {
      width: auto;
      text-align: left;
    }
  }
}
</style>
