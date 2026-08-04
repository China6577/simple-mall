import request from '@/utils/request'

/**
 * 购物车相关接口。
 */
export default {
  // 获取购物车列表及摘要
  getCart() {
    return request.get('/carts/')
  },

  // 添加商品到购物车
  // data: { sku_id, quantity }
  addToCart(data) {
    return request.post('/carts/items/', data)
  },

  // 修改购物车条目（数量/选中状态）
  // data: { quantity?, selected? }
  updateItem(id, data) {
    return request.put(`/carts/items/${id}/`, data)
  },

  // 删除购物车条目
  removeItem(id) {
    return request.delete(`/carts/items/${id}/`)
  },

  // 批量选中/取消选中
  // data: { item_ids: number[], selected: boolean }
  batchSelect(data) {
    return request.post('/carts/select/', data)
  }
}
