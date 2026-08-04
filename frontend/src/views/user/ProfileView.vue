<script setup>
import { ref, onMounted, reactive, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Delete, UserFilled, Camera } from '@element-plus/icons-vue'
import { regionData } from 'element-china-area-data'
import { useUserStore } from '@/stores/user'
import userApi from '@/api/user'
import Loading from '@/components/Loading.vue'

// 头像上传状态
const uploadingAvatar = ref(false)

async function uploadAvatar(options) {
  const file = options.file
  if (!file) return

  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return
  }

  uploadingAvatar.value = true
  try {
    const formData = new FormData()
    formData.append('avatar', file)
    // 保留当前用户名，避免被清空
    if (profileForm.username) formData.append('username', profileForm.username)

    const user = await userApi.updateMe(formData)
    userStore.setUser(user)
    ElMessage.success('头像已更新')
  } catch (error) {
    console.error(error)
    ElMessage.error('头像上传失败')
  } finally {
    uploadingAvatar.value = false
  }
}

const userStore = useUserStore()

const loading = ref(false)
const activeTab = ref('profile')

// 个人资料
const profileForm = reactive({
  username: ''
})
const profileFormRef = ref(null)
const savingProfile = ref(false)
const phonePattern = /^1[3-9]\d{9}$/

const profileRules = {
  username: [{ required: true, message: '请输入用户名', trigger: [] }]
}

// 修改密码
const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: [] }],
  new_password: [{ required: true, message: '请输入新密码', trigger: [] }],
  confirm_password: [{ required: true, message: '请确认新密码', trigger: [] }]
}
const passwordFormRef = ref(null)
const changingPassword = ref(false)

// 收货地址
const addresses = ref([])
const addressLoading = ref(false)
const addressDialogVisible = ref(false)
const addressFormRef = ref(null)
const editingAddressId = ref(null)
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

async function loadUserInfo() {
  loading.value = true
  try {
    const user = await userApi.getMe()
    userStore.setUser(user)
    profileForm.username = user.username || ''
  } catch (error) {
    console.error(error)
    ElMessage.error('获取用户信息失败')
  } finally {
    loading.value = false
  }
}

async function saveProfile() {
  const valid = await profileFormRef.value?.validate().catch(() => false)
  if (!valid) return

  savingProfile.value = true
  try {
    const user = await userApi.updateMe({
      username: profileForm.username
    })
    userStore.setUser(user)
    ElMessage.success('个人资料已更新')
    profileFormRef.value?.clearValidate()
  } catch (error) {
    // request.js 已统一提示错误，这里只打印日志
    console.error(error)
  } finally {
    savingProfile.value = false
  }
}

async function changePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.error('两次输入的新密码不一致')
    return
  }

  changingPassword.value = true
  try {
    await userApi.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })
    ElMessage.success('密码修改成功，请重新登录')
    passwordForm.old_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
    userStore.logout()
    window.location.href = '/login'
  } catch (error) {
    // request.js 已统一提示错误，这里只打印日志
    console.error(error)
  } finally {
    changingPassword.value = false
  }
}

async function loadAddresses() {
  addressLoading.value = true
  try {
    const res = await userApi.getAddresses()
    // 后端地址列表启用了分页，统一取 results；兼容直接返回数组的情况
    addresses.value = Array.isArray(res) ? res : res.results || []
  } catch (error) {
    console.error(error)
    ElMessage.error('获取地址失败')
  } finally {
    addressLoading.value = false
  }
}

function openAddressDialog(address = null) {
  editingAddressId.value = address?.id || null
  addressForm.receiver = address?.receiver || ''
  addressForm.phone = address?.phone || ''
  addressForm.province = address?.province || ''
  addressForm.city = address?.city || ''
  addressForm.district = address?.district || ''
  addressForm.detail = address?.detail || ''
  addressForm.zip_code = address?.zip_code || ''
  addressForm.is_default = address?.is_default || false
  addressDialogVisible.value = true
}

function resetAddressForm() {
  editingAddressId.value = null
  addressForm.receiver = ''
  addressForm.phone = ''
  addressForm.province = ''
  addressForm.city = ''
  addressForm.district = ''
  addressForm.detail = ''
  addressForm.zip_code = ''
  addressForm.is_default = false
}

async function saveAddress() {
  const valid = await addressFormRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    if (editingAddressId.value) {
      await userApi.updateAddress(editingAddressId.value, addressForm)
      ElMessage.success('地址已更新')
    } else {
      await userApi.createAddress(addressForm)
      ElMessage.success('地址已添加')
    }
    addressDialogVisible.value = false
    resetAddressForm()
    await loadAddresses()
  } catch (error) {
    // request.js 已统一提示错误，这里只打印日志
    console.error(error)
  }
}

async function deleteAddress(address) {
  try {
    await ElMessageBox.confirm('确定删除该收货地址吗？', '提示', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await userApi.deleteAddress(address.id)
    ElMessage.success('地址已删除')
    await loadAddresses()
  } catch (error) {
    if (error !== 'cancel') {
      console.error(error)
      ElMessage.error('删除失败')
    }
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  loadUserInfo()
  loadAddresses()
})
</script>

<template>
  <div class="profile-view">
    <div class="container">
      <div class="page-header">
        <h1 class="page-title">个人中心</h1>
        <p class="page-subtitle">管理您的账户信息、密码和收货地址</p>
      </div>

      <Loading v-if="loading" />

      <div v-else class="profile-layout">
        <!-- 用户信息卡片 -->
        <div class="profile-card user-card">
          <div class="user-meta">
            <el-upload
              class="avatar-uploader"
              action=""
              :show-file-list="false"
              accept="image/*"
              :http-request="uploadAvatar"
              :disabled="uploadingAvatar"
            >
              <el-avatar
                v-if="userStore.userInfo?.avatar_url"
                :size="80"
                :src="userStore.userInfo.avatar_url"
                class="user-avatar"
              />
              <el-avatar
                v-else
                :size="80"
                :icon="UserFilled"
                class="user-avatar"
              />
              <div class="avatar-mask">
                <el-icon><Camera /></el-icon>
                <span>更换</span>
              </div>
            </el-upload>
            <div class="user-info">
              <h2 class="username">{{ userStore.userInfo?.username || '用户' }}</h2>
              <p class="user-email">{{ userStore.userInfo?.email || '-' }}</p>
              <p class="user-date">注册于 {{ formatDate(userStore.userInfo?.date_joined) }}</p>
            </div>
          </div>
        </div>

        <!-- 标签页内容 -->
        <div class="profile-card tabs-card">
          <el-tabs v-model="activeTab" class="profile-tabs">
            <el-tab-pane label="个人资料" name="profile">
              <div class="form-section">
                <h3 class="section-title">基本信息</h3>
                <p class="section-desc">更新您的显示名称</p>
                <el-form
                  ref="profileFormRef"
                  :model="profileForm"
                  :rules="profileRules"
                  label-position="top"
                  class="profile-form"
                  @submit.prevent="saveProfile"
                >
                  <el-form-item label="用户名" prop="username">
                    <el-input
                      v-model="profileForm.username"
                      maxlength="150"
                      show-word-limit
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" :loading="savingProfile" @click="saveProfile">
                      保存资料
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-tab-pane>

            <el-tab-pane label="修改密码" name="password">
              <div class="form-section">
                <h3 class="section-title">修改密码</h3>
                <p class="section-desc">定期更新密码有助于保护账户安全</p>
                <el-form
                  ref="passwordFormRef"
                  :model="passwordForm"
                  :rules="passwordRules"
                  label-position="top"
                  class="profile-form"
                >
                  <el-form-item label="原密码" prop="old_password">
                    <el-input
                      v-model="passwordForm.old_password"
                      type="password"
                      show-password
                      @keyup.enter="changePassword"
                    />
                  </el-form-item>
                  <el-form-item label="新密码" prop="new_password">
                    <el-input
                      v-model="passwordForm.new_password"
                      type="password"
                      show-password
                      @keyup.enter="changePassword"
                    />
                  </el-form-item>
                  <el-form-item label="确认新密码" prop="confirm_password">
                    <el-input
                      v-model="passwordForm.confirm_password"
                      type="password"
                      show-password
                      @keyup.enter="changePassword"
                    />
                  </el-form-item>
                  <el-form-item>
                    <el-button type="primary" :loading="changingPassword" @click="changePassword">
                      修改密码
                    </el-button>
                  </el-form-item>
                </el-form>
              </div>
            </el-tab-pane>

            <el-tab-pane label="收货地址" name="addresses">
              <div class="address-section">
                <div class="address-header">
                  <div>
                    <h3 class="section-title">我的收货地址</h3>
                    <p class="section-desc">管理您的配送地址</p>
                  </div>
                  <el-button type="primary" @click="openAddressDialog()">新增地址</el-button>
                </div>

                <div v-if="addressLoading" class="address-loading">
                  <el-skeleton :rows="3" animated />
                </div>

                <div v-else-if="addresses.length === 0" class="empty-addresses">
                  暂无收货地址
                </div>

                <div v-else class="address-list">
                  <div
                    v-for="address in addresses"
                    :key="address.id"
                    class="address-item"
                    :class="{ default: address.is_default }"
                  >
                    <div class="address-main">
                      <div class="address-row">
                        <span class="address-receiver">{{ address.receiver }}</span>
                        <span class="address-phone">{{ address.phone }}</span>
                        <span
                          v-if="address.is_default"
                          class="default-tag"
                        >
                          默认
                        </span>
                      </div>
                      <div class="address-detail">
                        <span class="address-region">
                          {{ address.province }} {{ address.city }} {{ address.district }}
                        </span>
                        <span class="address-street">{{ address.detail }}</span>
                      </div>
                      <div v-if="address.zip_code" class="address-zip">
                        邮编：{{ address.zip_code }}
                      </div>
                    </div>
                    <div class="address-actions">
                      <el-tooltip content="编辑" placement="top">
                        <el-button
                          class="action-btn"
                          text
                          circle
                          size="default"
                          @click="openAddressDialog(address)"
                        >
                          <el-icon><Edit /></el-icon>
                        </el-button>
                      </el-tooltip>
                      <el-tooltip content="删除" placement="top">
                        <el-button
                          class="action-btn action-btn--danger"
                          text
                          circle
                          size="default"
                          @click="deleteAddress(address)"
                        >
                          <el-icon><Delete /></el-icon>
                        </el-button>
                      </el-tooltip>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </div>
  </div>

  <!-- 地址编辑弹窗 -->
  <el-dialog
    v-model="addressDialogVisible"
    :title="editingAddressId ? '编辑地址' : '新增地址'"
    width="560px"
    destroy-on-close
    class="address-dialog"
    @closed="resetAddressForm"
  >
    <el-form
      ref="addressFormRef"
      :model="addressForm"
      :rules="addressRules"
      label-position="top"
    >
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="收货人" prop="receiver">
            <el-input v-model="addressForm.receiver" @keyup.enter="saveAddress" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="手机号" prop="phone">
            <el-input
              v-model="addressForm.phone"
              maxlength="11"
              placeholder="请输入手机号"
              @keyup.enter="saveAddress"
            />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="省份" prop="province">
            <el-select
              v-model="addressForm.province"
              placeholder="请选择省份"
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
      <el-form-item label="邮编">
        <el-input v-model="addressForm.zip_code" />
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="addressForm.is_default">设为默认地址</el-checkbox>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="addressDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="saveAddress">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped lang="scss">
.profile-view {
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

.profile-layout {
  display: flex;
  flex-direction: column;
  gap: $space-6;
  animation: fadeInUp 0.6s 0.1s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.profile-card {
  background: $color-apple-white;
  border-radius: $radius-xl;
  padding: $space-8;
  border: none;
  box-shadow: $shadow-sm;
}

.user-card {
  .user-meta {
    display: flex;
    align-items: center;
    gap: $space-6;
  }

  .avatar-uploader {
    position: relative;
    cursor: pointer;
    border-radius: 50%;
    overflow: hidden;
    flex-shrink: 0;

    .user-avatar {
      background: $color-primary-soft;
      color: $color-primary;
      font-size: 30px;
      transition: transform $transition-base;
      border: 3px solid $color-apple-white;
      box-shadow: $shadow-sm;
    }

    .avatar-mask {
      position: absolute;
      inset: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 4px;
      background: rgba(0, 0, 0, 0.45);
      color: white;
      font-size: 12px;
      opacity: 0;
      transition: opacity $transition-base;

      .el-icon {
        font-size: 18px;
      }
    }

    &:hover {
      .user-avatar {
        transform: scale(1.05);
      }

      .avatar-mask {
        opacity: 1;
      }
    }
  }

  .user-info {
    .username {
      font-size: 24px;
      font-weight: 700;
      color: $text-primary;
      margin-bottom: $space-1;
      letter-spacing: -0.02em;
    }

    .user-email {
      font-size: 15px;
      color: $text-secondary;
      margin-bottom: $space-1;
    }

    .user-date {
      font-size: 13px;
      color: $text-tertiary;
    }
  }
}

.tabs-card {
  .profile-tabs {
    :deep(.el-tabs__header) {
      margin-bottom: $space-6;
      border-bottom: 1px solid $color-apple-border-light;
    }

    :deep(.el-tabs__nav-wrap::after) {
      display: none;
    }

    :deep(.el-tabs__item) {
      font-size: 15px;
      font-weight: 500;
      color: $text-secondary;
      padding: 0 $space-5;
      height: 44px;
      transition: color $transition-fast;

      &:hover {
        color: $text-primary;
      }

      &.is-active {
        color: $color-apple-blue;
        font-weight: 600;
      }
    }

    :deep(.el-tabs__active-bar) {
      background: $color-apple-blue;
      height: 2px;
      border-radius: 2px;
    }
  }
}

.form-section {
  max-width: 520px;
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  color: $text-primary;
  margin-bottom: $space-1;
  letter-spacing: -0.02em;
}

.section-desc {
  font-size: 14px;
  color: $text-secondary;
  margin-bottom: $space-6;
}

.profile-form {
  .el-form-item {
    margin-bottom: $space-5;
  }

  :deep(.el-form-item__label) {
    font-weight: 500;
    color: $text-primary;
    padding-bottom: $space-2;
    font-size: 14px;
  }

  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner) {
    border-radius: $radius-md;
    box-shadow: 0 0 0 1px $color-apple-border inset;
    transition: box-shadow $transition-base;
  }

  :deep(.el-input__wrapper) {
    padding: 4px 12px;

    &:hover,
    &.is-focus {
      box-shadow: 0 0 0 2px $color-apple-blue inset;
    }
  }

  :deep(.el-textarea__inner) {
    padding: 10px 12px;

    &:hover,
    &:focus {
      box-shadow: 0 0 0 2px $color-apple-blue inset;
    }
  }

  :deep(.el-input__inner) {
    height: 40px;
    font-size: 15px;
  }

  :deep(.el-button--primary) {
    border-radius: $radius-full;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 15px;
    background: $color-apple-blue;
    border: none;
    transition: all $transition-base;

    &:hover {
      background: $color-apple-blue-light;
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(0, 113, 227, 0.22);
    }
  }
}

.address-section {
  animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.address-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-6;

  .section-desc {
    margin-bottom: 0;
  }

  :deep(.el-button--primary) {
    border-radius: $radius-full;
    padding: 10px 22px;
    font-weight: 600;
    background: $color-apple-blue;
    border: none;
    transition: all $transition-base;

    &:hover {
      background: $color-apple-blue-light;
      transform: translateY(-1px);
      box-shadow: 0 8px 20px rgba(0, 113, 227, 0.22);
    }
  }
}

.empty-addresses {
  padding: $space-12 0;
  text-align: center;
  color: $text-secondary;
  font-size: 15px;
  background: $color-apple-gray;
  border-radius: $radius-lg;
}

.address-loading {
  padding: $space-4 0;
}

.address-list {
  display: flex;
  flex-direction: column;
  gap: $space-4;
}

.address-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: $space-6;
  border-radius: $radius-lg;
  background: $color-apple-gray;
  transition: all $transition-base;
  gap: $space-6;

  &:hover {
    background: $color-primary-soft;
    transform: translateY(-2px);
    box-shadow: $shadow-md;
  }

  &.default {
    background: $color-primary-soft;
    box-shadow: inset 0 0 0 1px rgba(0, 113, 227, 0.15);
  }

  .address-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: $space-3;
  }

  .address-row {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: $space-3;

    .address-receiver {
      font-size: 17px;
      font-weight: 700;
      color: $text-primary;
      letter-spacing: -0.01em;
    }

    .address-phone {
      font-size: 14px;
      color: $text-secondary;
      font-weight: 500;
    }

    .default-tag {
      font-size: 11px;
      font-weight: 600;
      color: $color-apple-blue;
      background: rgba(0, 113, 227, 0.1);
      padding: 2px 8px;
      border-radius: $radius-full;
    }
  }

  .address-detail {
    display: flex;
    flex-direction: column;
    gap: $space-1;

    .address-region {
      font-size: 14px;
      color: $text-secondary;
      line-height: 1.5;
    }

    .address-street {
      font-size: 15px;
      color: $text-primary;
      line-height: 1.6;
      font-weight: 500;
    }
  }

  .address-zip {
    font-size: 13px;
    color: $text-tertiary;
  }

  .address-actions {
    display: flex;
    gap: $space-2;
    flex-shrink: 0;
    padding-top: $space-1;

    .action-btn {
      width: 38px;
      height: 38px;
      color: $text-secondary;
      transition: all $transition-fast;
      border-radius: 50%;

      &:hover {
        color: $color-apple-blue;
        background: rgba(0, 113, 227, 0.08);
      }

      &--danger:hover {
        color: $color-danger;
        background: rgba(255, 59, 48, 0.08);
      }

      .el-icon {
        font-size: 16px;
      }
    }
  }
}

.address-dialog {
  :deep(.el-dialog) {
    border-radius: $radius-xl;
    box-shadow: $shadow-xl;
  }

  :deep(.el-dialog__header) {
    padding: $space-6 $space-6 $space-4;
    margin-right: 0;
  }

  :deep(.el-dialog__title) {
    font-size: 18px;
    font-weight: 700;
    color: $text-primary;
    letter-spacing: -0.01em;
  }

  :deep(.el-dialog__body) {
    padding: 0 $space-6 $space-4;
  }

  :deep(.el-dialog__footer) {
    padding: $space-4 $space-6 $space-6;
  }

  :deep(.el-form-item__label) {
    font-weight: 600;
    color: $text-primary !important;
    font-size: 14px;
    opacity: 1;
  }

  :deep(.el-form-item.is-required .el-form-item__label::before) {
    color: $color-danger;
  }

  :deep(.el-input__wrapper),
  :deep(.el-textarea__inner),
  :deep(.el-select .el-input__wrapper) {
    border-radius: $radius-md;
    box-shadow: 0 0 0 1px $color-apple-border inset;
    transition: box-shadow $transition-base;
  }

  :deep(.el-input__wrapper:hover),
  :deep(.el-input__wrapper.is-focus),
  :deep(.el-textarea__inner:hover),
  :deep(.el-textarea__inner:focus),
  :deep(.el-select .el-input.is-focus .el-input__wrapper) {
    box-shadow: 0 0 0 2px $color-apple-blue inset;
  }

  :deep(.el-button--primary) {
    background: $color-apple-blue;
    border: none;
    border-radius: $radius-full;
    padding: 10px 24px;
    font-weight: 600;

    &:hover {
      background: $color-apple-blue-light;
    }
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
  .profile-view {
    padding: $space-6 0 $space-10;
  }

  .profile-card {
    padding: $space-5;
    border-radius: $radius-lg;
  }

  .page-title {
    font-size: 28px;
  }

  .user-card .user-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: $space-4;
  }

  .tabs-card .profile-tabs :deep(.el-tabs__item) {
    padding: 0 $space-3;
    font-size: 14px;
  }

  .address-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $space-4;
  }

  .address-item {
    flex-direction: column;
    align-items: flex-start;
    gap: $space-4;
    padding: $space-5;

    .address-actions {
      width: 100%;
      justify-content: flex-end;
      padding-top: 0;
    }
  }

  .address-dialog :deep(.el-dialog) {
    width: 92% !important;
    border-radius: $radius-lg;
  }
}
</style>
