import { ref } from 'vue'

/**
 * 通用异步请求组合式函数。
 *
 * 自动管理 loading 和 error 状态，避免每个页面重复写 try/catch。
 */
export function useAsync(asyncFn) {
  const loading = ref(false)
  const error = ref(null)
  const data = ref(null)

  async function execute(...args) {
    loading.value = true
    error.value = null
    try {
      data.value = await asyncFn(...args)
      return data.value
    } catch (err) {
      error.value = err
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    error,
    data,
    execute
  }
}
