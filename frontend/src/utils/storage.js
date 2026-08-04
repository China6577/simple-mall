/**
 * 本地存储封装。
 *
 * 当前使用 localStorage 存放 Token（演示用途）。
 * 生产环境建议：
 * - Access Token 保存在内存中
 * - Refresh Token 放在 httpOnly Cookie 中
 */

const ACCESS_TOKEN_KEY = 'mall_access_token'
const REFRESH_TOKEN_KEY = 'mall_refresh_token'
const USER_KEY = 'mall_user'

const storage = {
  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  },
  setAccessToken(token) {
    localStorage.setItem(ACCESS_TOKEN_KEY, token)
  },
  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  },
  setRefreshToken(token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  },
  getUser() {
    const raw = localStorage.getItem(USER_KEY)
    return raw ? JSON.parse(raw) : null
  },
  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  },
  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }
}

export default storage
