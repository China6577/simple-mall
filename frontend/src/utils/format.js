/**
 * 通用格式化函数。
 */

/**
 * 金额格式化，保留两位小数，前缀 ¥。
 */
export function formatPrice(value) {
  const num = Number(value)
  if (Number.isNaN(num)) return '¥0.00'
  return `¥${num.toFixed(2)}`
}

/**
 * 日期时间格式化。
 */
export function formatDateTime(value) {
  if (!value) return '-'
  const date = new Date(value)
  return date.toLocaleString('zh-CN')
}
