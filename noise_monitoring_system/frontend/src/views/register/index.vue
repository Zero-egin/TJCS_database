<script setup>
import { ref, reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { DataLine, User, Lock, Iphone } from '@element-plus/icons-vue'

const userStore = useUserStore()
const router = useRouter()
const loading = ref(false)
const formRef = ref(null)

const form = reactive({
  username: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.password) {
          callback(new Error('两次输入密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleRegister = async (formEl) => {
  if (!formEl) return
  
  await formEl.validate(async (valid, fields) => {
    if (valid) {
      loading.value = true
      try {
        const registerData = {
          username: form.username,
          phone: form.phone,
          password: form.password
        }
        
        await userStore.register(registerData)

        ElMessage.success('注册成功，请登录')
        
        router.push('/login')
      } catch (error) {
        ElMessage.error(error.message || '注册失败')
      } finally {
        loading.value = false
      }
    } else {
      console.log('error submit!', fields)
    }
  })
}

const goToLogin = () => {
  router.push('/login')
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
        </div>
      </div>
      
      <div class="login-right">
        <div class="login-form-wrapper">
          <h2>用户注册</h2>
          <p class="welcome-text">创建您的账号</p>
          
          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-position="top"
            size="large"
            class="login-form"
          >
            <el-form-item prop="username">
              <el-input 
                v-model="form.username" 
                placeholder="用户名" 
                :prefix-icon="User"
              />
            </el-form-item>
            
            <el-form-item prop="phone">
              <el-input 
                v-model="form.phone" 
                placeholder="手机号" 
                :prefix-icon="Iphone"
              />
            </el-form-item>

            <el-form-item prop="password">
              <el-input 
                v-model="form.password" 
                type="password" 
                placeholder="密码" 
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="form.confirmPassword" 
                type="password" 
                placeholder="确认密码" 
                :prefix-icon="Lock"
                show-password
              />
            </el-form-item>

            <el-button 
              type="primary" 
              :loading="loading" 
              class="login-btn"
              @click="handleRegister(formRef)"
            >
              立即注册
            </el-button>
            
            <div class="form-footer">
              <span>已有账号？</span>
              <el-link type="primary" @click="goToLogin">去登录</el-link>
            </div>
          </el-form>
        </div>
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
  background: linear-gradient(135deg, #1f4037 0%, #99f2c8 100%);
  background-size: cover;
}

.login-content {
  display: flex;
  width: 900px;
  height: 650px; /* Increased height for register form */
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.login-left {
  flex: 1;
  background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  padding: 40px;
  position: relative;
  overflow: hidden;
}

.login-left::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('https://images.unsplash.com/photo-1480714378408-67cf0d13bc1b?ixlib=rb-4.0.3&auto=format&fit=crop&w=1770&q=80') center/cover no-repeat;
  opacity: 0.2;
}

.login-info {
  position: relative;
  z-index: 1;
  text-align: center;
}

.logo-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 20px;
}

.logo-wrapper h1 {
  font-size: 28px;
  margin-top: 15px;
  font-weight: 600;
  letter-spacing: 1px;
}

.subtitle {
  font-size: 16px;
  opacity: 0.8;
  letter-spacing: 2px;
}

.login-right {
  flex: 1;
  padding: 40px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow-y: auto; /* Allow scrolling if form is too long */
}

.login-form-wrapper {
  width: 100%;
  max-width: 360px;
  margin: 0 auto;
}

.login-form-wrapper h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.welcome-text {
  color: #666;
  margin-bottom: 30px;
  font-size: 14px;
}

.login-form {
  width: 100%;
}

.login-btn {
  width: 100%;
  margin-top: 10px;
  height: 45px;
  font-size: 16px;
  letter-spacing: 1px;
}

.form-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 14px;
  color: #666;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 5px;
}
</style>
