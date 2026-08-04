import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import DefaultLayout from '@/layouts/DefaultLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      component: DefaultLayout,
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('@/views/home/HomeView.vue')
        },
        {
          path: '/products',
          name: 'ProductList',
          component: () => import('@/views/product/ProductListView.vue')
        },
        {
          path: '/products/:id',
          name: 'ProductDetail',
          component: () => import('@/views/product/ProductDetailView.vue')
        },
        {
          path: '/search',
          name: 'SearchResult',
          component: () => import('@/views/product/SearchResultView.vue')
        },
        {
          path: '/cart',
          name: 'Cart',
          component: () => import('@/views/cart/CartView.vue')
        },
        {
          path: '/order/confirm',
          name: 'OrderConfirm',
          component: () => import('@/views/order/OrderConfirmView.vue')
        },
        {
          path: '/profile',
          name: 'Profile',
          component: () => import('@/views/user/ProfileView.vue')
        },
        {
          path: '/orders',
          name: 'OrderList',
          component: () => import('@/views/order/OrderListView.vue')
        },
        {
          path: '/coupons',
          name: 'CouponCenter',
          component: () => import('@/views/coupon/CouponCenterView.vue')
        },
        {
          path: '/orders/:orderNo',
          name: 'OrderDetail',
          component: () => import('@/views/order/OrderDetailView.vue')
        }
      ]
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/error/NotFoundView.vue')
    }
  ]
})

/**
 * 路由守卫：
 * - 未登录用户访问非公开页面时重定向到登录页
 * - 已登录用户访问登录/注册页时重定向到首页
 */
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isLoggedIn = userStore.isLoggedIn

  // 已登录用户访问登录/注册页时重定向到首页
  if (to.meta.public && isLoggedIn) {
    return next({ name: 'Home' })
  }

  // 未登录用户访问非公开页面时重定向到登录页
  if (!to.meta.public && !isLoggedIn) {
    return next({ name: 'Login', query: { redirect: to.fullPath } })
  }

  next()
})

export default router
