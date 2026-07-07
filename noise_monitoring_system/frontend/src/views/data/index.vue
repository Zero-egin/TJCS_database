<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore, PERMISSIONS } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Delete, Refresh } from '@element-plus/icons-vue'

const userStore = useUserStore()

// 数据导入相关
const uploadRef = ref(null)
const uploading = ref(false)
const importJobs = ref([])

// 数据清理相关（仅超级管理员）
const cleanForm = ref({
  startTime: '',
  endTime: '',
  pointId: null
})
const cleaning = ref(false)

// 上传处理
const handleUpload = async (options) => {
  uploading.value = true
  
  try {
    const formData = new FormData()
    formData.append('file', options.file)
    
    const response = await fetch('/api/readings/import', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      },
      body: formData
    })
    
    if (!response.ok) {
      let errorMessage = '导入失败'
      try {
        const error = await response.json()
        errorMessage = error.detail || errorMessage
      } catch (e) {
        // 响应不是 JSON 格式，尝试获取文本
        errorMessage = await response.text() || errorMessage
      }
      throw new Error(errorMessage)
    }
    
    const result = await response.json()
    // 检查任务状态
    if (result.status === 'failed') {
      ElMessage.warning(`导入完成但有错误，处理了 ${result.records_count || 0} 条数据`)
    } else {
      ElMessage.success(`导入成功，共处理 ${result.records_count || 0} 条数据`)
    }
    loadImportJobs()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    uploading.value = false
  }
}

// 加载导入历史
const loadImportJobs = async () => {
  // TODO: 实现导入历史加载
}

// 数据清理（仅超级管理员）
const handleClean = async () => {
  if (!userStore.hasPermission(PERMISSIONS.DATA_CLEAN)) {
    ElMessage.warning('您没有数据清理权限')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      '确定要清理选定时间范围内的错误数据吗？此操作不可恢复！',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    cleaning.value = true
    
    const params = new URLSearchParams()
    params.append('start_time', cleanForm.value.startTime)
    params.append('end_time', cleanForm.value.endTime)
    if (cleanForm.value.pointId) {
      params.append('point_id', cleanForm.value.pointId)
    }
    
    const response = await fetch(`/api/readings/clean?${params}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || '清理失败')
    }
    
    const result = await response.json()
    ElMessage.success(result.message)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message)
    }
  } finally {
    cleaning.value = false
  }
}

onMounted(() => {
  loadImportJobs()
})
</script>

<template>
  <div class="data-management">
    <h2>数据管理</h2>
    
    <!-- 数据导入区域 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>数据导入 (ETL)</span>
          <el-tag type="info" size="small">运维员及以上可操作</el-tag>
        </div>
      </template>
      
      <el-upload
        ref="uploadRef"
        class="upload-area"
        drag
        accept=".csv"
        :auto-upload="true"
        :show-file-list="false"
        :http-request="handleUpload"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload" :size="60">
          <Upload />
        </el-icon>
        <div class="el-upload__text">
          将 CSV 文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 CSV 格式，包含字段: point_id, measured_at, db_value, temperature, humidity
          </div>
        </template>
      </el-upload>
      
      <el-progress 
        v-if="uploading" 
        :percentage="100" 
        status="success" 
        :indeterminate="true"
        style="margin-top: 20px;"
      />
    </el-card>
    
    <!-- 数据清理区域（仅超级管理员） -->
    <el-card 
      v-if="userStore.hasPermission(PERMISSIONS.DATA_CLEAN)" 
      class="section-card"
    >
      <template #header>
        <div class="card-header">
          <span>数据清理</span>
          <el-tag type="danger" size="small">仅超级管理员可操作</el-tag>
        </div>
      </template>
      
      <el-form :model="cleanForm" label-width="100px">
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="cleanForm.startTime"
            type="datetime"
            placeholder="选择开始时间"
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="cleanForm.endTime"
            type="datetime"
            placeholder="选择结束时间"
          />
        </el-form-item>
        <el-form-item label="监测点ID">
          <el-input-number
            v-model="cleanForm.pointId"
            :min="1"
            placeholder="可选，留空清理所有点位"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button 
            type="danger" 
            :loading="cleaning"
            :icon="Delete"
            @click="handleClean"
          >
            清理错误数据
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 导入历史 -->
    <el-card class="section-card">
      <template #header>
        <div class="card-header">
          <span>导入历史</span>
          <el-button :icon="Refresh" size="small" @click="loadImportJobs">刷新</el-button>
        </div>
      </template>
      
      <el-table :data="importJobs" stripe>
        <el-table-column prop="id" label="任务ID" width="80" />
        <el-table-column prop="source" label="数据来源" />
        <el-table-column prop="rows_processed" label="处理行数" width="100" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'completed' ? 'success' : 'warning'">
              {{ row.status === 'completed' ? '完成' : '进行中' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>
      
      <el-empty v-if="importJobs.length === 0" description="暂无导入记录" />
    </el-card>
  </div>
</template>

<style scoped>
.data-management {
  padding: 20px;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

:deep(.el-upload-dragger) {
  width: 100%;
}
</style>
