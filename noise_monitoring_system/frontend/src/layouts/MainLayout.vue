<script setup>
import { ref, computed } from 'vue'
import { RouterView, useRouter, useRoute } from 'vue-router'
import { useUserStore, ROLES, PERMISSIONS } from '@/stores/user'
import { Monitor, DataLine, Bell, Setting, SwitchButton, Odometer, Upload, User } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()

// 根据角色动态生成菜单
const menuItems = computed(() => {
  const items = [
    {
      index: '/dashboard',
      icon: Odometer,
      label: '仪表盘',
      show: true  // 所有用户可见
    },
    {
      index: '/monitor',
      icon: Monitor,
      label: '实时监测',
      show: true  // 所有用户可见
    },
    {
      index: '/alerts',
      icon: Bell,
      label: '报警管理',
      show: true  // 所有用户可见，但操作权限不同
    },
    {
      index: '/stats',
      icon: DataLine,
      label: '统计分析',
      show: true  // 所有用户可见
    },
    {
      index: '/data',
      icon: Upload,
      label: '数据管理',
      show: userStore.hasPermission(PERMISSIONS.DATA_IMPORT)  // 运维员及以上
    },
    {
      index: '/admin',
      icon: Setting,
      label: '系统管理',
      show: userStore.hasPermission(PERMISSIONS.USER_MANAGE)  // 仅超级管理员
    },
    {
      index: '/profile',
      icon: User,
      label: '个人中心',
      show: true  // 所有用户可见
    }
  ]
  
  return items.filter(item => item.show)
})

const handleLogout = () => {
  userStore.logout()
}
</script>

<template>
  <el-container>
    <el-aside width="200px">
      <div class="logo">
        <h2>噪声治理平台</h2>
      </div>
      <el-menu
        :default-active="route.path"
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        router
      >
        <el-menu-item 
          v-for="item in menuItems" 
          :key="item.index" 
          :index="item.index"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="breadcrumb">
          {{ route.meta.title }}
        </div>
        <div class="user-info">
          <el-tag 
            :type="userStore.isSuperAdmin ? 'danger' : userStore.isAreaOperator ? 'warning' : 'info'"
            size="small"
            class="role-tag"
          >
            {{ userStore.roleLabel }}
          </el-tag>
          <span class="username">{{ userStore.userInfo.username || '用户' }}</span>
          <el-button link @click="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
        </div>
      </el-header>
      <el-main>
        <RouterView />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #2b3649;
}
.logo h2 {
  color: #fff;
  font-size: 18px;
  margin: 0;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}
.role-tag {
  margin-right: 5px;
}
.username {
  color: #606266;
}
</style>
