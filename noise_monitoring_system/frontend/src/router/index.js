import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '../layouts/MainLayout.vue'
import LoginView from '../views/login/index.vue'
import RegisterView from '../views/register/index.vue'
import DashboardView from '../views/dashboard/index.vue'
import { ROLES, PERMISSIONS } from '../stores/user'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true }  // 公开页面，无需登录
    },
    {
      path: '/register',
      name: 'register',
      component: RegisterView,
      meta: { public: true }  // 公开页面，无需登录
    },
    {
      path: '/',
      component: MainLayout,
      redirect: '/dashboard',
      children: [
        {
          path: 'dashboard',
          name: 'dashboard',
          component: DashboardView,
          meta: { 
            title: '仪表盘'
            // 所有登录用户可访问，无需特殊权限
          }
        },
        {
          path: 'monitor',
          name: 'monitor',
          component: () => import('../views/monitor/index.vue'),
          meta: { 
            title: '实时监测'
            // 所有登录用户可访问
          }
        },
        {
          path: 'alerts',
          name: 'alerts',
          component: () => import('../views/alerts/index.vue'),
          meta: { 
            title: '报警管理'
            // 所有登录用户可查看，但操作权限在页面内控制
          }
        },
        {
          path: 'stats',
          name: 'stats',
          component: () => import('../views/stats/index.vue'),
          meta: { 
            title: '统计分析'
            // 所有登录用户可访问
          }
        },
        {
          path: 'data',
          name: 'data',
          component: () => import('../views/data/index.vue'),
          meta: { 
            title: '数据管理',
            // 运维员及以上可访问
            roles: [ROLES.SUPER_ADMIN, ROLES.AREA_OPERATOR]
          }
        },
        {
          path: 'admin',
          name: 'admin',
          component: () => import('../views/admin/index.vue'),
          meta: { 
            title: '系统管理',
            // 仅超级管理员可访问
            roles: [ROLES.SUPER_ADMIN]
          }
        },
        {
          path: 'profile',
          name: 'profile',
          component: () => import('../views/profile/index.vue'),
          meta: { 
            title: '个人中心'
            // 所有登录用户可访问
          }
        }
      ]
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('../views/error/403.vue'),
      meta: { public: true, title: '无权访问' }
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('../views/error/404.vue'),
      meta: { public: true, title: '页面不存在' }
    }
  ]
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
  
  // 如果已登录且访问登录页，跳转到首页
  if (to.name === 'login' && token) {
    next({ path: '/' })
    return
  }

  // 公开页面直接放行
  if (to.meta.public) {
    next()
    return
  }
  
  // 未登录跳转登录页
  if (!token) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }
  
  // 检查角色权限（仅当路由配置了roles时才检查）
  if (to.meta.roles && to.meta.roles.length > 0) {
    const userRole = userInfo.role_name
    if (!userRole || !to.meta.roles.includes(userRole)) {
      next({ name: 'forbidden' })
      return
    }
  }
  
  // 没有配置权限要求的页面，登录用户都可以访问
  next()
})

export default router
