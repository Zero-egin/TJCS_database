<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Lock, User, Edit } from '@element-plus/icons-vue'

const userStore = useUserStore()

// 密码修改表单
const passwordForm = ref({
  old_password: '',
  new_password: '',
  confirm_password: ''
})
const passwordFormRef = ref(null)
const changingPassword = ref(false)

// 个人信息
const userInfoForm = ref({
  username: '',
  email: '',
  role_name: '',
  created_at: ''
})

// 表单验证规则
const passwordRules = {
  old_password: [
    { required: true, message: '请输入原密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.value.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 修改密码
const handleChangePassword = async () => {
  try {
    await passwordFormRef.value.validate()
    
    changingPassword.value = true
    
    const response = await fetch('/api/auth/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`
      },
      body: JSON.stringify({
        old_password: passwordForm.value.old_password,
        new_password: passwordForm.value.new_password
      })
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '修改失败')
    }
    
    ElMessage.success('密码修改成功')
    passwordForm.value = {
      old_password: '',
      new_password: '',
      confirm_password: ''
    }
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  } finally {
    changingPassword.value = false
  }
}

// 加载用户信息
const loadUserInfo = () => {
  userInfoForm.value = {
    username: userStore.userInfo.username || '',
    email: userStore.userInfo.email || '',
    role_name: userStore.roleLabel,
    created_at: userStore.userInfo.created_at || ''
  }
}

onMounted(() => {
  loadUserInfo()
  userStore.refreshUserInfo()
})
</script>

<template>
  <div class="profile-page">
    <h2>个人中心</h2>
    
    <!-- 个人信息 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><User /></el-icon>
          <span>个人信息</span>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">
          {{ userInfoForm.username }}
        </el-descriptions-item>
        <el-descriptions-item label="邮箱">
          {{ userInfoForm.email || '未设置' }}
        </el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag 
            :type="userStore.isSuperAdmin ? 'danger' : userStore.isAreaOperator ? 'warning' : 'info'"
          >
            {{ userInfoForm.role_name }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ userInfoForm.created_at }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <!-- 权限信息 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><Lock /></el-icon>
          <span>我的权限</span>
        </div>
      </template>
      
      <div class="permissions-list">
        <el-tag 
          v-for="permission in userStore.permissions" 
          :key="permission"
          class="permission-tag"
          type="success"
        >
          {{ getPermissionLabel(permission) }}
        </el-tag>
        <el-empty v-if="userStore.permissions.length === 0" description="暂无权限" />
      </div>
    </el-card>
    
    <!-- 修改密码 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <el-icon><Edit /></el-icon>
          <span>修改密码</span>
        </div>
      </template>
      
      <el-form 
        ref="passwordFormRef"
        :model="passwordForm" 
        :rules="passwordRules"
        label-width="100px"
        style="max-width: 400px;"
      >
        <el-form-item label="原密码" prop="old_password">
          <el-input 
            v-model="passwordForm.old_password" 
            type="password" 
            show-password
            placeholder="请输入原密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="new_password">
          <el-input 
            v-model="passwordForm.new_password" 
            type="password" 
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input 
            v-model="passwordForm.confirm_password" 
            type="password" 
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="primary" 
            :loading="changingPassword"
            @click="handleChangePassword"
          >
            修改密码
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
// 权限标签映射
const PERMISSION_LABELS = {
  user_manage: '用户管理',
  password_change: '修改密码',
  area_manage: '区域管理',
  point_manage: '监测点管理',
  point_view: '查看监测点',
  data_import: '数据导入',
  data_clean: '数据清理',
  alert_resolve: '处理报警',
  alert_manage: '报警管理',
  stats_view: '统计查看'
}

function getPermissionLabel(permission) {
  return PERMISSION_LABELS[permission] || permission
}
</script>

<style scoped>
.profile-page {
  padding: 20px;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.permissions-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.permission-tag {
  margin: 0;
}
</style>
