import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import storage from '@/utils/storage'

/**
 * 用户状态管理。
 *
 * 提供登录态、Token、用户信息的响应式存储，
 * 页面组件通过 useUserStore 读取或修改。
 */
export const useUserStore = defineStore('user', () => {
  // State
  const accessToken = ref(storage.getAccessToken())
  const refreshToken = ref(storage.getRefreshToken())
  const userInfo = ref(storage.getUser())

  // Getters
  const isLoggedIn = computed(() => !!accessToken.value)
  const isAdmin = computed(() => userInfo.value?.role === 'admin')

  // Actions
  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    storage.setAccessToken(access)
    storage.setRefreshToken(refresh)
  }

  function setUser(user) {
    userInfo.value = user
    storage.setUser(user)
  }

  function logout() {
    accessToken.value = ''
    refreshToken.value = ''
    userInfo.value = null
    storage.clear()
  }

  return {
    accessToken,
    refreshToken,
    userInfo,
    isLoggedIn,
    isAdmin,
    setTokens,
    setUser,
    logout
  }
})
