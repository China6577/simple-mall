import { ref } from 'vue'
import { defineStore } from 'pinia'

/**
 * 全局应用状态。
 */
export const useAppStore = defineStore('app', () => {
  const loading = ref(false)
  const title = ref(import.meta.env.VITE_APP_TITLE || '企业电商系统')

  function setLoading(value) {
    loading.value = value
  }

  return {
    loading,
    title,
    setLoading
  }
})
