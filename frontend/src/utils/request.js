/**
 * Axios 实例封装。
 *
 * 职责：
 * - 统一 baseURL、超时、Content-Type
 * - 请求拦截器：自动注入 Access Token
 * - 响应拦截器：处理统一错误码、Token 刷新、401 退出登录
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'
import storage from './storage'

// 是否正在刷新 Token，防止多个请求同时触发刷新
let isRefreshing = false
// 等待刷新完成的请求队列
let refreshSubscribers = []

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  },
  transformRequest: [(data, headers) => {
    // 上传文件时让浏览器自动设置 Content-Type（含 boundary）
    if (data instanceof FormData) {
      delete headers['Content-Type']
      return data
    }
    // 普通对象需要序列化为 JSON，否则请求体会变成 [object Object]
    if (data && typeof data === 'object') {
      return JSON.stringify(data)
    }
    return data
  }]

})

/**
 * 请求拦截器：从本地存储读取 Access Token 并附加到请求头。
 */
request.interceptors.request.use(
  (config) => {
    const token = storage.getAccessToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

/**
 * 响应拦截器：
 * 1. 2xx 直接返回 data
 * 2. 401 时尝试用 Refresh Token 刷新 Access Token
 * 3. 刷新失败或无法刷新时，清空登录态并跳转登录页
 */
request.interceptors.response.use(
  (response) => {
    // 兼容 204 No Content 等空响应体
    if (response.status === 204 || response.data === '' || response.data === null || response.data === undefined) {
      return {}
    }

    // 后端统一返回 { code, message, data }
    const res = response.data
    if (res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message))
    }
    return res.data
  },
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status
    const data = error.response?.data

    // 401 且不是刷新接口本身，尝试刷新 Token
    if (status === 401 && originalRequest && !originalRequest._retry) {
      if (isRefreshing) {
        // 把请求加入队列，等待刷新完成后重试
        return new Promise((resolve) => {
          refreshSubscribers.push((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(request(originalRequest))
          })
        })
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        const newToken = await refreshAccessToken()
        refreshSubscribers.forEach((callback) => callback(newToken))
        refreshSubscribers = []
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return request(originalRequest)
      } catch (refreshError) {
        // 刷新失败，退出登录
        const userStore = useUserStore()
        userStore.logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    const message = extractErrorMessage(data) || '请求失败，请稍后重试'
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/**
 * 从后端错误响应中提取最友好的第一条错误信息。
 * 兼容 { message }, { detail }, { field: [msg] } 等多种 DRF 返回格式。
 */
function extractErrorMessage(data) {
  if (!data) return ''
  if (typeof data === 'string') return data
  if (data.message) return data.message
  if (data.detail) return data.detail

  const fieldLabels = {
    username: '用户名',
    email: '邮箱',
    password: '密码',
    old_password: '原密码',
    new_password: '新密码',
    confirm_password: '确认密码',
    phone: '手机号',
    receiver: '收货人',
    province: '省份',
    city: '城市',
    district: '区县',
    detail: '详细地址'
  }

  for (const key of ['non_field_errors', ...Object.keys(data)]) {
    const value = data[key]
    if (Array.isArray(value) && value.length > 0) {
      return key === 'non_field_errors' ? value[0] : `${fieldLabels[key] || key}：${value[0]}`
    }
    if (typeof value === 'string' && value) {
      return key === 'non_field_errors' ? value : `${fieldLabels[key] || key}：${value}`
    }
  }

  return ''
}

/**
 * 调用后端刷新接口换取新的 Access Token。
 */
async function refreshAccessToken() {
  const refreshToken = storage.getRefreshToken()
  if (!refreshToken) {
    throw new Error('缺少 Refresh Token')
  }

  // 使用独立 axios 实例，避免触发当前拦截器形成死循环
  const { data } = await axios.post(
    `${request.defaults.baseURL}/auth/token/refresh/`,
    { refresh: refreshToken }
  )

  if (data.code !== 0 || !data.data?.access) {
    throw new Error(data.message || '刷新 Token 失败')
  }

  const { access, refresh } = data.data
  storage.setAccessToken(access)
  if (refresh) {
    storage.setRefreshToken(refresh)
  }
  return access
}

export default request
