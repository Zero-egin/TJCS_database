<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus, Edit, Delete, Check, Close, Refresh } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const activeTab = ref('users')
const loading = ref(false)

// 编辑用户对话框
const editDialogVisible = ref(false)
const editLoading = ref(false)
const editingUser = ref(null)
const editFormRef = ref(null)
const editForm = reactive({
  email: '',
  phone: '',
  real_name: '',
  role_id: null,
  status: ''
})

// 新增运维员对话框
const addDialogVisible = ref(false)
const addLoading = ref(false)
const addFormRef = ref(null)
const addForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  real_name: '',
  phone: '',
  email: ''
})

// 编辑表单验证规则
const editRules = {
  email: [
    { 
      pattern: /^$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, 
      message: '请输入正确的邮箱格式', 
      trigger: 'blur' 
    }
  ],
  phone: [
    { 
      pattern: /^$|^1[3-9]\d{9}$/, 
      message: '请输入正确的手机号（11位）', 
      trigger: 'blur' 
    }
  ]
}

// 新增运维员表单验证规则
const addRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== addForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^$|^1[3-9]\d{9}$/, message: '请输入正确的手机号', trigger: 'blur' }
  ],
  email: [
    { pattern: /^$|^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/, message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

// 角色列表
const roleList = [
  { id: 1, name: 'super_admin', label: '超级管理员' },
  { id: 2, name: 'area_operator', label: '区域运维员' },
  { id: 3, name: 'public_user', label: '普通用户' }
]

// 状态列表
const statusList = [
  { value: 'active', label: '正常' },
  { value: 'inactive', label: '停用' },
  { value: 'locked', label: '锁定' },
  { value: 'pending', label: '待审核' }
]

// 根据用户角色获取可用的状态列表（普通用户没有待审核状态）
const getAvailableStatusList = () => {
  // 如果当前编辑的用户是普通用户，不显示待审核选项
  if (editingUser.value?.role_name === 'public_user' || editForm.role_id === 3) {
    return statusList.filter(s => s.value !== 'pending')
  }
  return statusList
}

// 角色名称映射
const roleMap = {
  super_admin: '超级管理员',
  area_operator: '区域运维员',
  public_user: '普通用户'
}

// 状态映射
const statusMap = {
  active: { label: '正常', type: 'success' },
  inactive: { label: '停用', type: 'info' },
  locked: { label: '锁定', type: 'danger' },
  pending: { label: '待审核', type: 'warning' }
}

// 判断是否可以编辑用户（超级管理员不能被编辑）
const canEditUser = (user) => {
  return user.role_name !== 'super_admin'
}

// 判断是否可以删除用户（超级管理员不能被删除）
const canDeleteUser = (user) => {
  return user.role_name !== 'super_admin'
}

// 打开新增运维员对话框
const openAddDialog = () => {
  addForm.username = ''
  addForm.password = ''
  addForm.confirmPassword = ''
  addForm.real_name = ''
  addForm.phone = ''
  addForm.email = ''
  addDialogVisible.value = true
}

// 提交新增运维员
const handleAddSubmit = async () => {
  if (addFormRef.value) {
    try {
      await addFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  addLoading.value = true
  try {
    const response = await fetch('/api/users', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        username: addForm.username,
        password: addForm.password,
        real_name: addForm.real_name,
        phone: addForm.phone || null,
        email: addForm.email || null,
        role: 'area_operator',
        status: 'active'
      })
    })
    
    if (response.ok) {
      ElMessage.success('新增运维员成功')
      addDialogVisible.value = false
      fetchUsers()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '新增失败')
    }
  } catch (error) {
    ElMessage.error('新增失败')
  } finally {
    addLoading.value = false
  }
}

// 用户管理数据
const userList = ref([])

// 设备管理数据
const deviceList = ref([])
const deviceLoading = ref(false)

// 设备对话框
const deviceDialogVisible = ref(false)
const deviceDialogTitle = ref('新增设备')
const deviceLoading2 = ref(false)
const deviceFormRef = ref(null)
const editingDevice = ref(null)
const deviceForm = reactive({
  serial_no: '',
  model: '',
  status: 'active'
})

// 设备表单验证规则
const deviceRules = {
  serial_no: [
    { required: true, message: '请输入设备编号', trigger: 'blur' },
    { min: 2, max: 50, message: '设备编号长度为2-50个字符', trigger: 'blur' }
  ],
  model: [
    { max: 100, message: '设备型号最多100个字符', trigger: 'blur' }
  ]
}

// 设备状态选项
const deviceStatusList = [
  { value: 'active', label: '在线' },
  { value: 'inactive', label: '离线' },
  { value: 'maintenance', label: '维护中' }
]

// 获取用户列表
const fetchUsers = async () => {
  loading.value = true
  try {
    const response = await fetch('/api/users', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      userList.value = await response.json()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '获取用户列表失败')
    }
  } catch (error) {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

// 获取设备列表
const fetchDevices = async () => {
  deviceLoading.value = true
  try {
    const response = await fetch('/api/devices', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      deviceList.value = data.map(device => ({
        id: device.id,
        serial_no: device.serial_no,
        code: device.serial_no || device.device_code || `DEV-${device.id}`,
        name: device.model || '未命名设备',
        model: device.model || '',
        type: '声级计',
        status: device.status,
        installDate: device.installed_at?.split('T')[0] || '-'
      }))
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '获取设备列表失败')
    }
  } catch (error) {
    ElMessage.error('获取设备列表失败')
  } finally {
    deviceLoading.value = false
  }
}

// 打开新增设备对话框
const openAddDeviceDialog = () => {
  deviceDialogTitle.value = '新增设备'
  editingDevice.value = null
  deviceForm.serial_no = ''
  deviceForm.model = ''
  deviceForm.status = 'active'
  deviceDialogVisible.value = true
}

// 打开编辑设备对话框
const openEditDeviceDialog = (row) => {
  deviceDialogTitle.value = '编辑设备'
  editingDevice.value = row
  deviceForm.serial_no = row.serial_no || row.code || ''
  deviceForm.model = row.model || row.name || ''
  deviceForm.status = row.status || 'active'
  deviceDialogVisible.value = true
}

// 提交设备表单（新增或编辑）
const handleDeviceSubmit = async () => {
  if (deviceFormRef.value) {
    try {
      await deviceFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  deviceLoading2.value = true
  try {
    const isEdit = !!editingDevice.value
    const url = isEdit ? `/api/devices/${editingDevice.value.id}` : '/api/devices'
    const method = isEdit ? 'PUT' : 'POST'
    
    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        serial_no: deviceForm.serial_no,
        model: deviceForm.model || null,
        status: deviceForm.status
      })
    })
    
    if (response.ok) {
      ElMessage.success(isEdit ? '编辑设备成功' : '新增设备成功')
      deviceDialogVisible.value = false
      fetchDevices()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || (isEdit ? '编辑失败' : '新增失败'))
    }
  } catch (error) {
    ElMessage.error('操作失败')
  } finally {
    deviceLoading2.value = false
  }
}

// 删除设备
const handleDeleteDevice = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除设备 "${row.code}" 吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    const response = await fetch(`/api/devices/${row.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('删除成功')
      fetchDevices()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchUsers()
  fetchDevices()
})

const handleEdit = (row) => {
  editingUser.value = row
  editForm.email = row.email || ''
  editForm.phone = row.phone || ''
  editForm.real_name = row.real_name || ''
  editForm.role_id = row.role_id
  editForm.status = row.status
  editDialogVisible.value = true
}

const handleEditSubmit = async () => {
  // 先验证表单
  if (editFormRef.value) {
    try {
      await editFormRef.value.validate()
    } catch (error) {
      return
    }
  }
  
  editLoading.value = true
  try {
    const response = await fetch(`/api/users/${editingUser.value.id}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: editForm.email || null,
        phone: editForm.phone || null,
        real_name: editForm.real_name || null,
        role_id: editForm.role_id,
        status: editForm.status
      })
    })
    
    if (response.ok) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      fetchUsers() // 刷新列表
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '更新失败')
    }
  } catch (error) {
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

const handleApprove = async (row) => {
  try {
    await ElMessageBox.confirm(`确认通过用户 "${row.username}" 的运维人员申请吗?`, '审核确认', {
      confirmButtonText: '确定通过',
      cancelButtonText: '取消',
      type: 'success',
    })
    
    const response = await fetch(`/api/users/${row.id}/approve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('已通过申请')
      fetchUsers() // 刷新列表
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '操作失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleReject = async (row) => {
  try {
    await ElMessageBox.confirm(`确认拒绝用户 "${row.username}" 的运维人员申请吗?`, '审核确认', {
      confirmButtonText: '确定拒绝',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    const response = await fetch(`/api/users/${row.id}/reject`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.warning('已拒绝申请')
      fetchUsers() // 刷新列表
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '操作失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除用户 "${row.username}" 吗?`, '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    
    const response = await fetch(`/api/users/${row.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('删除成功')
      fetchUsers() // 刷新列表
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}
</script>

<template>
  <div class="admin-container">
    <el-card>
      <el-tabs v-model="activeTab">
        <!-- 用户管理 -->
        <el-tab-pane label="用户管理" name="users">
          <div class="tab-toolbar">
            <el-button type="primary" :icon="Plus" @click="openAddDialog">新增运维员</el-button>
            <el-button :icon="Refresh" @click="fetchUsers">刷新</el-button>
          </div>
          <el-table :data="userList" style="width: 100%" v-loading="loading">
            <el-table-column prop="username" label="用户名" />
            <el-table-column prop="real_name" label="真实姓名" />
            <el-table-column prop="phone" label="手机号" />
            <el-table-column prop="role_name" label="角色">
              <template #default="scope">
                {{ roleMap[scope.row.role_name] || scope.row.role_name }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="statusMap[scope.row.status]?.type || 'info'">
                  {{ statusMap[scope.row.status]?.label || scope.row.status }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" width="180">
              <template #default="scope">
                {{ new Date(scope.row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="280">
              <template #default="scope">
                <template v-if="scope.row.status === 'pending'">
                  <el-button size="small" type="success" :icon="Check" @click="handleApprove(scope.row)">通过</el-button>
                  <el-button size="small" type="danger" :icon="Close" @click="handleReject(scope.row)">拒绝</el-button>
                </template>
                <el-button 
                  size="small" 
                  :icon="Edit" 
                  :disabled="!canEditUser(scope.row)"
                  :title="!canEditUser(scope.row) ? '不能编辑超级管理员' : ''"
                  @click="handleEdit(scope.row)"
                >编辑</el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  :icon="Delete" 
                  :disabled="!canDeleteUser(scope.row)"
                  :title="!canDeleteUser(scope.row) ? '不能删除超级管理员' : ''"
                  @click="handleDelete(scope.row)"
                >删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- 设备管理 -->
        <el-tab-pane label="设备管理" name="devices">
          <div class="tab-toolbar">
            <el-button type="primary" :icon="Plus" @click="openAddDeviceDialog">新增设备</el-button>
            <el-button :icon="Refresh" @click="fetchDevices" style="margin-left: 10px">刷新</el-button>
          </div>
          <el-table :data="deviceList" style="width: 100%" v-loading="deviceLoading">
            <el-table-column prop="code" label="设备编号" />
            <el-table-column prop="name" label="设备型号" />
            <el-table-column prop="type" label="设备类型" />
            <el-table-column prop="status" label="状态">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'active' ? 'success' : (scope.row.status === 'maintenance' ? 'warning' : 'info')">
                  {{ scope.row.status === 'active' ? '在线' : (scope.row.status === 'maintenance' ? '维护中' : '离线') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="installDate" label="安装日期" />
            <el-table-column label="操作" width="180">
              <template #default="scope">
                <el-button size="small" :icon="Edit" @click="openEditDeviceDialog(scope.row)">编辑</el-button>
                <el-button size="small" type="danger" :icon="Delete" @click="handleDeleteDevice(scope.row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="deviceList.length === 0 && !deviceLoading" description="暂无设备数据" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <!-- 编辑用户对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑用户" width="500px">
      <el-form ref="editFormRef" :model="editForm" :rules="editRules" label-width="80px">
        <el-form-item label="用户名">
          <el-input :value="editingUser?.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="真实姓名">
          <el-input v-model="editForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role_id" placeholder="请选择角色" style="width: 100%">
            <el-option 
              v-for="role in roleList" 
              :key="role.id" 
              :label="role.label" 
              :value="role.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option 
              v-for="status in getAvailableStatusList()" 
              :key="status.value" 
              :label="status.label" 
              :value="status.value" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEditSubmit">保存</el-button>
      </template>
    </el-dialog>
    
    <!-- 新增运维员对话框 -->
    <el-dialog v-model="addDialogVisible" title="新增运维员" width="500px">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="80px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="addForm.username" placeholder="请输入用户名（3-20个字符）" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="addForm.password" type="password" placeholder="请输入密码（至少6位）" show-password />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input v-model="addForm.confirmPassword" type="password" placeholder="请再次输入密码" show-password />
        </el-form-item>
        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="addForm.real_name" placeholder="请输入真实姓名" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="addForm.phone" placeholder="请输入手机号（选填）" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="addForm.email" placeholder="请输入邮箱（选填）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="addLoading" @click="handleAddSubmit">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 设备对话框（新增/编辑） -->
    <el-dialog v-model="deviceDialogVisible" :title="deviceDialogTitle" width="500px">
      <el-form ref="deviceFormRef" :model="deviceForm" :rules="deviceRules" label-width="80px">
        <el-form-item label="设备编号" prop="serial_no">
          <el-input v-model="deviceForm.serial_no" placeholder="请输入设备编号" :disabled="!!editingDevice" />
        </el-form-item>
        <el-form-item label="设备型号" prop="model">
          <el-input v-model="deviceForm.model" placeholder="请输入设备型号（选填）" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="deviceForm.status" placeholder="请选择状态" style="width: 100%">
            <el-option 
              v-for="status in deviceStatusList" 
              :key="status.value" 
              :label="status.label" 
              :value="status.value" 
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deviceDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="deviceLoading2" @click="handleDeviceSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.tab-toolbar {
  margin-bottom: 15px;
}
</style>
