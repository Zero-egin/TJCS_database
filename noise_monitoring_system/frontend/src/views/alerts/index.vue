<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Location, Delete, Refresh } from '@element-plus/icons-vue'
import BaseMap from '@/components/BaseMap.vue'
import { useUserStore, PERMISSIONS } from '@/stores/user'

const userStore = useUserStore()
const loading = ref(false)

// 告警数据
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

const filters = reactive({
  keyword: '',
  status: '',
  areaType: '',
  minLevel: '',
  dateRange: []
})

const dialogVisible = ref(false)
const mapDialogVisible = ref(false)
const currentAlert = ref(null)
const currentMapPoints = ref([])

const handleForm = reactive({
  action: '',
  remark: '',
  handler: ''  // 处置人
})

// 获取告警列表
const fetchAlerts = async () => {
  try {
    loading.value = true
    const params = new URLSearchParams()
    params.append('skip', (currentPage.value - 1) * pageSize.value)
    params.append('limit', pageSize.value)
    
    if (filters.status) {
      params.append('status', filters.status)
    }
    
    // 添加日期范围筛选
    if (filters.dateRange && filters.dateRange.length === 2) {
      const startDate = filters.dateRange[0]
      const endDate = filters.dateRange[1]
      if (startDate) {
        params.append('start_time', new Date(startDate).toISOString())
      }
      if (endDate) {
        params.append('end_time', new Date(endDate).toISOString())
      }
    }
    
    const response = await fetch(`/api/alerts?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      const data = await response.json()
      // 处理返回数据格式
      tableData.value = (Array.isArray(data) ? data : data.items || []).map(item => {
        // 计算持续时间
        let duration = '-'
        const triggeredAt = item.triggered_at || item.created_at || item.alert_time
        const resolvedAt = item.resolved_at
        if (triggeredAt && resolvedAt) {
          const start = new Date(triggeredAt)
          const end = new Date(resolvedAt)
          const diffMs = end - start
          if (diffMs > 0) {
            const diffMins = Math.floor(diffMs / 60000)
            const diffHours = Math.floor(diffMins / 60)
            const diffDays = Math.floor(diffHours / 24)
            if (diffDays > 0) {
              duration = `${diffDays}天${diffHours % 24}小时`
            } else if (diffHours > 0) {
              duration = `${diffHours}小时${diffMins % 60}分钟`
            } else {
              duration = `${diffMins}分钟`
            }
          }
        } else if (triggeredAt && item.status === 'open') {
          // 待处理状态，显示已经过的时间
          const start = new Date(triggeredAt)
          const now = new Date()
          const diffMs = now - start
          const diffMins = Math.floor(diffMs / 60000)
          const diffHours = Math.floor(diffMins / 60)
          const diffDays = Math.floor(diffHours / 24)
          if (diffDays > 0) {
            duration = `待处理 ${diffDays}天`
          } else if (diffHours > 0) {
            duration = `待处理 ${diffHours}小时`
          } else {
            duration = `待处理 ${diffMins}分钟`
          }
        }
        
        return {
          id: item.id,
          time: triggeredAt,
          pointName: item.point_name || item.point?.name || `点位#${item.point_id}`,
          areaType: item.area_type || item.point?.area?.name || '-',
          value: item.db_value || item.db_level || item.reading_value || 0,
          threshold: item.threshold_db || item.threshold || 60,
          duration: duration,
          status: item.status,
          handler: item.resolved_by_name || item.handler || '-',
          lat: item.latitude || item.point?.latitude || 22.54,
          lng: item.longitude || item.point?.longitude || 114.06,
          remark: item.remark || item.description || ''
        }
      })
      total.value = data.total || tableData.value.length
    }
  } catch (error) {
    console.error('获取告警数据失败:', error)
    ElMessage.error('获取告警数据失败')
  } finally {
    loading.value = false
  }
}

// 筛选后的数据 (前端筛选关键词和分贝等级)
const filteredData = computed(() => {
  let data = tableData.value
  if (filters.keyword) {
    const kw = filters.keyword.toLowerCase()
    data = data.filter(item => item.pointName.toLowerCase().includes(kw))
  }
  if (filters.minLevel) {
    const minDb = parseInt(filters.minLevel)
    data = data.filter(item => item.value > minDb)
  }
  if (filters.areaType) {
    data = data.filter(item => item.areaType.includes(filters.areaType))
  }
  return data
})

const handleSearch = () => {
  currentPage.value = 1
  fetchAlerts()
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchAlerts()
}

const openHandleDialog = (row) => {
  currentAlert.value = row
  handleForm.action = ''
  handleForm.remark = ''
  handleForm.handler = userStore.user?.username || ''  // 默认使用当前用户名
  dialogVisible.value = true
}

const openMapDialog = (row) => {
  currentMapPoints.value = [{
    id: row.id,
    name: row.pointName,
    lat: row.lat,
    lng: row.lng,
    value: row.value,
    status: 'alarm',
    address: row.areaType
  }]
  mapDialogVisible.value = true
}

const submitHandle = async () => {
  if (!handleForm.action) {
    ElMessage.warning('请填写处置措施')
    return
  }
  if (!handleForm.handler) {
    ElMessage.warning('请填写处置人')
    return
  }
  
  try {
    const response = await fetch(`/api/alerts/${currentAlert.value.id}/resolve`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        notes: handleForm.action + (handleForm.remark ? ` | ${handleForm.remark}` : ''),
        handler: handleForm.handler
      })
    })
    
    if (response.ok) {
      ElMessage.success('处置成功')
      dialogVisible.value = false
      fetchAlerts()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '处置失败')
    }
  } catch (error) {
    console.error('处置失败:', error)
    ElMessage.error('处置失败')
  }
}

// 删除报警（仅超级管理员）
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除报警记录 #${row.id} 吗？此操作不可恢复！`,
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await fetch(`/api/alerts/${row.id}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('删除成功')
      fetchAlerts()
    } else {
      const error = await response.json()
      ElMessage.error(error.detail || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 归档报警（仅超级管理员）
const handleArchive = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要归档报警记录 #${row.id} 吗？归档后将不会在默认列表中显示。`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    const response = await fetch(`/api/alerts/${row.id}/archive`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    
    if (response.ok) {
      ElMessage.success('归档成功')
      fetchAlerts()
    } else {
      const data = await response.json()
      ElMessage.error(data.detail || '归档失败')
    }
  } catch (error) {
    // 用户取消操作
    if (error !== 'cancel') {
      console.error('归档失败:', error)
    }
  }
}

const getStatusType = (status) => {
  if (status === 'open') return 'danger'
  if (status === 'archived') return 'info'
  return 'success'
}

const getStatusText = (status) => {
  if (status === 'open') return '待处理'
  if (status === 'archived') return '已归档'
  return '已处置'
}

onMounted(() => {
  fetchAlerts()
})
</script>

<template>
  <div class="alerts-container">
    <!-- 多维筛选工具栏 -->
    <div class="toolbar">
      <el-input
        v-model="filters.keyword"
        placeholder="搜索点位名称"
        style="width: 180px"
        :prefix-icon="Search"
      />
      
      <el-select v-model="filters.areaType" placeholder="区域类别" style="width: 120px; margin-left: 10px" clearable>
        <el-option label="居住区" value="residential" />
        <el-option label="商业区" value="commercial" />
        <el-option label="工业区" value="industrial" />
        <el-option label="混合区" value="mixed" />
      </el-select>

      <el-select v-model="filters.minLevel" placeholder="分贝等级" style="width: 120px; margin-left: 10px" clearable>
        <el-option label="> 50 dB" value="50" />
        <el-option label="> 60 dB" value="60" />
        <el-option label="> 70 dB" value="70" />
        <el-option label="> 80 dB" value="80" />
      </el-select>

      <el-select v-model="filters.status" placeholder="处理状态" style="width: 120px; margin-left: 10px" clearable>
        <el-option label="待处理" value="open" />
        <el-option label="已处置" value="resolved" />
        <el-option label="已归档" value="archived" />
      </el-select>

      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        style="margin-left: 10px; width: 240px;"
      />
      
      <el-button type="primary" style="margin-left: 10px" @click="handleSearch">查询</el-button>
      <el-button :icon="Refresh" style="margin-left: 10px" @click="fetchAlerts">刷新</el-button>
    </div>

    <el-card class="table-card" v-loading="loading">
      <el-table :data="filteredData" style="width: 100%" stripe>
        <el-table-column prop="time" label="报警时间" width="170" />
        <el-table-column prop="pointName" label="监测点位" width="150" />
        <el-table-column prop="areaType" label="区域类别" width="100" />
        <el-table-column prop="value" label="监测值(dB)" width="110">
          <template #default="scope">
            <span style="color: #F56C6C; font-weight: bold;">{{ scope.row.value }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="threshold" label="阈值" width="80" />
        <el-table-column prop="duration" label="持续时间" width="100" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">{{ getStatusText(scope.row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handler" label="处置人" width="100" />
        <el-table-column label="操作" fixed="right" min-width="180">
          <template #default="scope">
            <el-button 
              size="small" 
              :icon="Location"
              @click="openMapDialog(scope.row)"
            >
              定位
            </el-button>
            <el-button 
              v-if="scope.row.status === 'open' && userStore.hasPermission(PERMISSIONS.ALERT_RESOLVE)"
              size="small" 
              type="primary" 
              @click="openHandleDialog(scope.row)"
            >
              处置
            </el-button>
            <el-dropdown 
              v-if="userStore.hasPermission(PERMISSIONS.ALERT_MANAGE)"
              style="margin-left: 10px;"
            >
              <el-button size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="handleArchive(scope.row)">归档</el-dropdown-item>
                  <el-dropdown-item @click="handleDelete(scope.row)" style="color: #F56C6C;">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 权限提示：只对普通用户显示（既没有处置权限也没有管理权限） -->
      <el-alert 
        v-if="!userStore.hasPermission(PERMISSIONS.ALERT_RESOLVE) && !userStore.hasPermission(PERMISSIONS.ALERT_MANAGE)"
        type="info"
        :closable="false"
        style="margin-top: 15px;"
      >
        <template #title>
          您当前为只读模式，无法进行报警处置操作。如需操作权限，请联系管理员。
        </template>
      </el-alert>
      
      <div class="pagination">
        <el-pagination 
          background 
          layout="total, prev, pager, next" 
          :total="total" 
          :page-size="pageSize"
          :current-page="currentPage"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 处置弹窗 -->
    <el-dialog v-model="dialogVisible" title="报警处置" width="500px">
      <el-form :model="handleForm" label-width="80px">
        <el-form-item label="报警点位">
          <el-input :value="currentAlert?.pointName" disabled />
        </el-form-item>
        <el-form-item label="报警时间">
          <el-input :value="currentAlert?.time" disabled />
        </el-form-item>
        <el-form-item label="处置人" required>
          <el-input v-model="handleForm.handler" placeholder="请输入处置人姓名" />
        </el-form-item>
        <el-form-item label="处置措施" required>
          <el-input v-model="handleForm.action" placeholder="例如：已通知相关单位整改" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="handleForm.remark" type="textarea" placeholder="其他说明信息（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitHandle">确认处置</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 地图定位弹窗 -->
    <el-dialog v-model="mapDialogVisible" title="报警点位溯源" width="800px" destroy-on-close>
      <div style="height: 500px;">
        <BaseMap 
          v-if="mapDialogVisible"
          :points="currentMapPoints" 
          :center="[currentMapPoints[0]?.lat, currentMapPoints[0]?.lng]"
          :zoom="16"
        />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  margin-bottom: 15px;
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
