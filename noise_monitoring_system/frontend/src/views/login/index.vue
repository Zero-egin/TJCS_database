<script setup>
import { ref, reactive } from 'vue'
import { useUserStore, ROLE_LABELS } from '@/stores/user'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataLine, Monitor, Bell, Odometer, User, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()
const route = useRoute()
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.username || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    const data = await userStore.login(form.username, form.password)
    const roleName = ROLE_LABELS[data.user.role_name] || '用户'
    ElMessage.success(`欢迎回来，${roleName} ${data.user.username}`)
    
    // 跳转到原来要访问的页面或首页
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (error) {
    ElMessage.error(error.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <div class="login-content">
      <div class="login-left">
        <div class="login-info">
          <div class="logo-wrapper">
            <el-icon :size="40" color="#fff"><DataLine /></el-icon>
            <h1>城市噪声环境治理平台</h1>
          </div>
          <p class="subtitle">智慧监测 · 科学治理 · 宁静生活</p>
          <ul class="features">
            <li><el-icon><Monitor /></el-icon> 实时噪声监测与数据采集</li>
            <li><el-icon><Bell /></el-icon> 智能超标报警与联动处置</li>
            <li><el-icon><Odometer /></el-icon> 多维数据分析与决策支持</li>
          </ul>
        </div>
        <div class="bg-decoration"></div>
      </div>
      
      <div class="login-right">
        <el-card class="login-card" shadow="never">
          <template #header>
            <div class="card-header">
              <h2>欢迎登录</h2>
              <p>请输入您的账号和密码</p>
            </div>
          </template>
          <el-form :model="form" label-width="0" @keyup.enter="handleLogin" size="large">
            <el-form-item>
              <el-input v-model="form.username" placeholder="请输入用户名" prefix-icon="User" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password" type="password" placeholder="请输入密码" prefix-icon="Lock" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="loading" class="login-btn" @click="handleLogin">
                立即登录
              </el-button>
            </el-form-item>
            <div class="register-link">
              <span>没有账号？</span>
              <el-link type="primary" @click="$router.push('/register')">立即注册</el-link>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  height: 100vh;
  width: 100vw;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1c2434 0%, #2d3a4b 100%);
  overflow: hidden;
  position: relative;
}

/* 背景装饰 */
.login-container::before {
  content: '';
  position: absolute;
  top: -10%;
  left: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
}

.login-container::after {
  content: '';
  position: absolute;
  bottom: -10%;
  right: -10%;
  width: 50%;
  height: 50%;
  background: radial-gradient(circle, rgba(64, 158, 255, 0.1) 0%, rgba(0, 0, 0, 0) 70%);
  border-radius: 50%;
}

.login-content {
  display: flex;
  width: 900px;
  height: 550px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  z-index: 1;
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #304156 0%, #1f2d3d 100%);
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  color: #fff;
  position: relative;
}

.logo-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.logo-wrapper h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  line-height: 1.2;
}

.subtitle {
  font-size: 16px;
  opacity: 0.8;
  margin-bottom: 40px;
  letter-spacing: 1px;
}

.features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.features li {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 15px;
  opacity: 0.9;
}

.login-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background: #fff;
}

.login-card {
  width: 100%;
  max-width: 360px;
  border: none;
}

.card-header {
  text-align: center;
  margin-bottom: 20px;
}

.card-header h2 {
  font-size: 24px;
  color: #303133;
  margin: 0 0 10px 0;
}

.card-header p {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.login-btn {
  width: 100%;
  font-size: 16px;
  padding: 12px 0;
}

.register-link {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 10px;
  font-size: 14px;
  color: #606266;
  gap: 5px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .login-content {
    width: 90%;
    height: auto;
    flex-direction: column;
  }
  
  .login-left {
    padding: 30px;
    text-align: center;
  }
  
  .logo-wrapper {
    justify-content: center;
  }
  
  .features {
    display: none;
  }
  
  .login-right {
    padding: 30px;
  }
}
</style>
