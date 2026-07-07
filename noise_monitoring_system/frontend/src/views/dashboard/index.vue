<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Calendar } from '@element-plus/icons-vue'

const userStore = useUserStore()
const chartRef = ref(null)
const loading = ref(false)

// 数据时间范围
const dataRange = ref({
  min: null,
  max: null
})

// 当前选择的日期
const selectedDate = ref(null)

// 概览统计数据
const stats = ref({
  todayAvgDb: '-',
  pendingAlerts: 0,
  dataDate: '',
  todayReadings: 0,
  exceedRate: '-'
})

// 区域噪声排名
const areaRankings = ref([])

// 获取数据时间范围
const fetchDataRange = async () => {
  try {
    const response = await fetch('/api/stats/data-range', {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      dataRange.value.min = data.min_time ? new Date(data.min_time) : null
      dataRange.value.max = data.max_time ? new Date(data.max_time) : null
      // 默认选择最新日期
      if (dataRange.value.max && !selectedDate.value) {
        selectedDate.value = new Date(dataRange.value.max)
      }
    }
  } catch (error) {
    console.error('获取数据时间范围失败:', error)
  }
}

// 获取概览数据
const fetchOverview = async () => {
  try {
    let url = '/api/stats/overview'
    if (selectedDate.value) {
      // 使用选中日期的全天时间范围
      const startDate = new Date(selectedDate.value)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(selectedDate.value)
      endDate.setHours(23, 59, 59, 999)
      url += `?start_time=${encodeURIComponent(startDate.toISOString())}&end_time=${encodeURIComponent(endDate.toISOString())}`
    }
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      stats.value.todayAvgDb = data.today_avg_db ? `${data.today_avg_db} dB` : '-'
      stats.value.pendingAlerts = data.active_alerts || 0
      stats.value.dataDate = data.data_date || ''
      stats.value.todayReadings = data.today_readings || 0
      stats.value.exceedRate = data.exceed_rate != null ? `${parseFloat(data.exceed_rate).toFixed(1)}%` : '-'
    }
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 获取区域排名 (使用area-stats获取真实的平均分贝)
const fetchAreaRanking = async () => {
  try {
    let url = '/api/stats/area-stats'
    if (selectedDate.value) {
      // 使用选中日期的全天时间范围（与其他数据保持一致）
      const startDate = new Date(selectedDate.value)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(selectedDate.value)
      endDate.setHours(23, 59, 59, 999)
      url += `?start_time=${encodeURIComponent(startDate.toISOString())}&end_time=${encodeURIComponent(endDate.toISOString())}`
    }
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      // 筛选有数据的区域，按avg_db排序取前5
      areaRankings.value = data
        .filter(item => item.avg_db != null)
        .sort((a, b) => (b.avg_db || 0) - (a.avg_db || 0))
        .slice(0, 5)
        .map(item => ({
          name: item.area_name || item.name,
          val: Math.round((item.avg_db || 0) * 10) / 10
        }))
    }
  } catch (error) {
    console.error('获取区域排名失败:', error)
  }
}

// 获取24小时趋势
const fetchHourlyTrend = async () => {
  try {
    let url = '/api/stats/hourly-trend'
    if (selectedDate.value) {
      const startDate = new Date(selectedDate.value)
      startDate.setHours(0, 0, 0, 0)
      const endDate = new Date(selectedDate.value)
      endDate.setHours(23, 59, 59, 999)
      url += `?start_time=${startDate.toISOString()}&end_time=${endDate.toISOString()}`
    }
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data && data.length > 0) {
        const chart = echarts.init(chartRef.value)
        chart.setOption({
          title: { text: `噪声趋势 (${stats.value.dataDate || '当日'})` },
          tooltip: { trigger: 'axis' },
          xAxis: { 
            type: 'category', 
            data: data.map(item => `${String(item.hour || 0).padStart(2, '0')}:00`)
          },
          yAxis: { type: 'value', name: '分贝(dB)' },
          series: [{ 
            data: data.map(item => item.avg_db || item.avg || 0), 
            type: 'line', 
            smooth: true,
            areaStyle: { opacity: 0.3 }
          }]
        })
      } else {
        initDefaultChart()
      }
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
    initDefaultChart()
  }
}

const initDefaultChart = () => {
  const chart = echarts.init(chartRef.value)
  chart.setOption({
    title: { text: '24小时噪声趋势' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'] },
    yAxis: { type: 'value', name: '分贝(dB)' },
    series: [{ data: [], type: 'line', smooth: true }]
  })
}

// 日期改变时刷新数据
const handleDateChange = async () => {
  loading.value = true
  await Promise.all([
    fetchOverview(),
    fetchAreaRanking(),
    fetchHourlyTrend()
  ])
  loading.value = false
}

// 禁用超出数据范围的日期
const disabledDate = (date) => {
  if (!dataRange.value.min || !dataRange.value.max) return false
  return date < dataRange.value.min || date > dataRange.value.max
}

// 格式化日期范围显示
const formatDateRange = () => {
  if (!dataRange.value.min || !dataRange.value.max) return '加载中...'
  const min = dataRange.value.min.toLocaleDateString('zh-CN')
  const max = dataRange.value.max.toLocaleDateString('zh-CN')
  return `${min} ~ ${max}`
}

onMounted(async () => {
  loading.value = true
  await fetchDataRange()
  await Promise.all([
    fetchOverview(),
    fetchAreaRanking(),
    fetchHourlyTrend()
  ])
  loading.value = false
})
</script>

<template>
  <div class="dashboard" v-loading="loading">
    <!-- 日期选择器 -->
    <div class="date-selector">
      <el-card shadow="never" class="date-card">
        <div class="date-info">
          <span class="label">数据时间范围：</span>
          <span class="range">{{ formatDateRange() }}</span>
        </div>
        <div class="date-picker">
          <span class="label">选择查看日期：</span>
          <el-date-picker
            v-model="selectedDate"
            type="date"
            placeholder="选择日期"
            :disabled-date="disabledDate"
            @change="handleDateChange"
            style="width: 180px"
          />
        </div>
      </el-card>
    </div>

    <el-row :gutter="20">
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>当日平均噪声</span>
              <el-tag size="small" v-if="stats.dataDate">{{ stats.dataDate }}</el-tag>
            </div>
          </template>
          <div class="stat-value">{{ stats.todayAvgDb }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>待处理告警</template>
          <div class="stat-value warning">{{ stats.pendingAlerts }} 条</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>当日监测次数</template>
          <div class="stat-value">{{ stats.todayReadings }} 次</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <template #header>当日超标率</template>
          <div class="stat-value" :class="parseFloat(stats.exceedRate) > 10 ? 'danger' : 'success'">{{ stats.exceedRate }}</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card>
          <div ref="chartRef" style="height: 400px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>区域噪声排名</span>
              <el-tag size="small" v-if="stats.dataDate">{{ stats.dataDate }}</el-tag>
            </div>
          </template>
          <el-table :data="areaRankings" :show-header="areaRankings.length > 0">
            <el-table-column prop="name" label="区域" />
            <el-table-column prop="val" label="噪声(dB)" />
          </el-table>
          <el-empty v-if="areaRankings.length === 0" description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.date-selector {
  margin-bottom: 20px;
}
.date-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.date-card :deep(.el-card__body) {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
}
.date-info, .date-picker {
  display: flex;
  align-items: center;
  color: white;
}
.date-info .label, .date-picker .label {
  margin-right: 10px;
  font-weight: 500;
}
.date-info .range {
  font-weight: bold;
  font-size: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  text-align: center;
}
.danger { color: #F56C6C; }
.success { color: #67C23A; }
.warning { color: #E6A23C; }
.mt-20 { margin-top: 20px; }
</style>
