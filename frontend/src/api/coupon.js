import request from '@/utils/request'

/**
 * 优惠券相关接口。
 */
export default {
  // 可领取优惠券列表
  getCoupons(params) {
    return request.get('/coupons/', { params })
  },

  // 我的优惠券列表
  // params: { status?: 'unused' | 'used' | 'expired' }
  getMyCoupons(params) {
    return request.get('/coupons/my/', { params })
  },

  // 领取优惠券
  claimCoupon(couponId) {
    return request.post(`/coupons/${couponId}/claim/`)
  },

  // 优惠券试算
  // data: { coupon_ids: number[], total_amount: string }
  calculate(data) {
    return request.post('/coupons/calculate/', data)
  },

  // 查询购物车可用的优惠券
  // cartItemIds: number[]
  getAvailableForCart(cartItemIds) {
    const ids = Array.isArray(cartItemIds) ? cartItemIds.join(',') : cartItemIds
    return request.get('/coupons/available/', { params: { cart_item_ids: ids } })
  }
}
