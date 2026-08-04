import request from '@/utils/request'

export default {
  // 分类列表
  getCategories() {
    return request.get('/products/categories/')
  },

  // 品牌列表
  getBrands() {
    return request.get('/products/brands/')
  },

  // 商品列表（支持分页、筛选、搜索、排序）
  // params: { page, page_size, category, brand, keyword, ordering, hot, new }
  getProducts(params) {
    return request.get('/products/', { params })
  },

  // 商品详情
  getProductDetail(id) {
    return request.get(`/products/${id}/`)
  },

  // 热门商品
  getHotProducts() {
    return request.get('/products/hot/')
  }
}
