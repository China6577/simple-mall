import request from '@/utils/request'

export default {
  callback(data) {
    return request.post('/payments/callback/', data)
  }
}
