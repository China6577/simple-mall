import request from '@/utils/request'

export default {
  getMe() {
    return request.get('/auth/me/')
  },
  updateMe(data) {
    return request.patch('/auth/me/', data)
  },
  changePassword(data) {
    return request.post('/auth/change-password/', data)
  },

  // 收货地址
  getAddresses() {
    return request.get('/auth/addresses/')
  },
  createAddress(data) {
    return request.post('/auth/addresses/', data)
  },
  updateAddress(id, data) {
    return request.put(`/auth/addresses/${id}/`, data)
  },
  deleteAddress(id) {
    return request.delete(`/auth/addresses/${id}/`)
  }
}
