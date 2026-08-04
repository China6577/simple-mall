import request from '@/utils/request'

/**
 * 订单相关接口。
 */
export default {
  // 创建订单
  // data: { cart_item_ids: number[], address_id: number, remark?: string, idempotency_key?: string }
  createOrder(data) {
    return request.post('/orders/', data)
  },

  // 订单列表
  getOrders(params) {
    return request.get('/orders/', { params })
  },

  // 订单详情
  getOrderDetail(orderNo) {
    return request.get(`/orders/${orderNo}/`)
  },

  // 取消订单
  cancelOrder(orderNo) {
    return request.post(`/orders/${orderNo}/cancel/`)
  },

  // 模拟支付
  payOrder(orderNo) {
    return request.post(`/orders/${orderNo}/pay/`)
  },

  // 确认收货
  confirmOrder(orderNo) {
    return request.post(`/orders/${orderNo}/confirm/`)
  },

  // 删除订单（软删除）
  deleteOrder(orderNo) {
    return request.delete(`/orders/${orderNo}/delete/`)
  }
}
