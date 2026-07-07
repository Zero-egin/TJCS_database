import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

/**
 * 角色常量
 */
export const ROLES = {
  SUPER_ADMIN: 'super_admin',      // 超级管理员
  AREA_OPERATOR: 'area_operator',  // 区域运维员
  PUBLIC_USER: 'public_user'       // 普通用户
}

/**
 * 权限常量
 */
export const PERMISSIONS = {
  // 用户管理
  USER_MANAGE: 'user_manage',           // 增删用户 / 重置他人密码
  PASSWORD_CHANGE: 'password_change',   // 修改个人密码
  
  // 区域管理
  AREA_MANAGE: 'area_manage',           // 设置区域范围与噪声阈值
  
  // 监测点管理
  POINT_MANAGE: 'point_manage',         // 部署/删除点位坐标
  POINT_VIEW: 'point_view',             // 查看点位详情
  
  // 数据导入
  DATA_IMPORT: 'data_import',           // 执行大规模数据集导入 (ETL)
  DATA_CLEAN: 'data_clean',             // 清理/修正历史错误数据
  
  // 报警管理
  ALERT_RESOLVE: 'alert_resolve',       // 标记报警处理状态 (Resolve)
  ALERT_MANAGE: 'alert_manage',         // 删除/归档报警记录
  
  // 统计分析
  STATS_VIEW: 'stats_view',             // 查看全市治理看板与报表
}

/**
 * 角色显示名称映射
 */
export const ROLE_LABELS = {
  [ROLES.SUPER_ADMIN]: '超级管理员',
  [ROLES.AREA_OPERATOR]: '区域运维员',
  [ROLES.PUBLIC_USER]: '普通用户'
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const userInfo = ref(JSON.parse(localStorage.getItem('userInfo') || '{}'))
  const permissions = ref(JSON.parse(localStorage.getItem('permissions') || '[]'))
  const router = useRouter()

  // 计算属性：用户角色
  const role = computed(() => userInfo.value.role_name || '')
  
  // 计算属性：角色显示名称
  const roleLabel = computed(() => ROLE_LABELS[role.value] || '未知角色')
  
  // 计算属性：是否为超级管理员
  const isSuperAdmin = computed(() => role.value === ROLES.SUPER_ADMIN)
  
  // 计算属性：是否为区域运维员
  const isAreaOperator = computed(() => role.value === ROLES.AREA_OPERATOR)
  
  // 计算属性：是否为普通用户
  const isPublicUser = computed(() => role.value === ROLES.PUBLIC_USER)
  
  // 计算属性：是否为运维人员（运维员或管理员）
  const isOperator = computed(() => 
    role.value === ROLES.SUPER_ADMIN || role.value === ROLES.AREA_OPERATOR
  )

  /**
   * 检查是否有指定权限
   * @param {string} permission 权限标识
   * @returns {boolean}
   */
  function hasPermission(permission) {
    return permissions.value.includes(permission)
  }

  /**
   * 检查是否有任一指定权限
   * @param {string[]} permissionList 权限标识列表
   * @returns {boolean}
   */
  function hasAnyPermission(permissionList) {
    return permissionList.some(p => permissions.value.includes(p))
  }

  /**
   * 用户登录
   * @param {string} username 用户名
   * @param {string} password 密码
   */
  async function login(username, password) {
    // 调用后端登录接口
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      let errorMsg = '登录失败'
      try {
        const error = await response.json()
        errorMsg = error.detail || errorMsg
      } catch (e) {
        errorMsg = `请求失败 (${response.status}): ${response.statusText || '服务器无响应'}`
      }
      throw new Error(errorMsg)
    }
    
    const data = await response.json()
    
    token.value = data.access_token
    userInfo.value = data.user
    permissions.value = data.permissions || []
    
    localStorage.setItem('token', token.value)
    localStorage.setItem('userInfo', JSON.stringify(userInfo.value))
    localStorage.setItem('permissions', JSON.stringify(permissions.value))
    
    return data
  }

  /**
   * 用户注册
   * @param {Object} registerData 注册信息
   */
  async function register(registerData) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(registerData)
    })
    
    if (!response.ok) {
      let errorMsg = '注册失败'
      try {
        const error = await response.json()
        errorMsg = error.detail || errorMsg
      } catch (e) {
        errorMsg = `请求失败 (${response.status}): ${response.statusText || '服务器无响应'}`
      }
      throw new Error(errorMsg)
    }
    
    return await response.json()
  }

  /**
   * 用户登出
   */
  function logout() {
    token.value = ''
    userInfo.value = {}
    permissions.value = []
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('permissions')
    router.push('/login')
  }

  /**
   * 刷新用户信息
   */
  async function refreshUserInfo() {
    if (!token.value) return
    
    try {
      const response = await fetch('/api/auth/me', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        userInfo.value = data
        localStorage.setItem('userInfo', JSON.stringify(data))
      }
    } catch (error) {
      console.error('刷新用户信息失败:', error)
    }
  }

  /**
   * 刷新权限信息
   */
  async function refreshPermissions() {
    if (!token.value) return
    
    try {
      const response = await fetch('/api/auth/me/permissions', {
        headers: {
          'Authorization': `Bearer ${token.value}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        permissions.value = data
        localStorage.setItem('permissions', JSON.stringify(data))
      }
    } catch (error) {
      console.error('刷新权限信息失败:', error)
    }
  }

  return { 
    token, 
    userInfo, 
    permissions,
    role,
    roleLabel,
    isSuperAdmin,
    isAreaOperator,
    isPublicUser,
    isOperator,
    hasPermission,
    hasAnyPermission,
    login, 
    register,
    logout,
    refreshUserInfo,
    refreshPermissions
  }
})
