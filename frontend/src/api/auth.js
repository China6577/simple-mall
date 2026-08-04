import request from '@/utils/request'

export default {
  register(data) {
    return request.post('/auth/register/', data)
  },
  login(data) {
    return request.post('/auth/login/', data)
  },
  refresh(refreshToken) {
    return request.post('/auth/token/refresh/', { refresh: refreshToken })
  },
  logout(refreshToken) {
    return request.post('/auth/logout/', { refresh: refreshToken })
  }
}
