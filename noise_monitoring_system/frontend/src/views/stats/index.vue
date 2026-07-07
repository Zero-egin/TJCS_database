<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import BaseChart from '@/components/BaseChart.vue'
import { Download, Refresh } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()
const loading = ref(false)
const analysisMode = ref('daily')  // 'daily' 或 'monthly'
const selectedDate = ref(null)
const selectedMonth = ref(null)
const startHour = ref(0)
const endHour = ref(23)
const activeTab = ref('trend')

// 小时选项 (0-23)
const hourOptions = Array.from({ length: 24 }, (_, i) => ({
  value: i,
  label: `${String(i).padStart(2, '0')}:00`
}))

// 图表引用
const trendChartRef = ref(null)
const rankChartRef = ref(null)

// 监听 tab 切换，触发图表 resize
watch(activeTab, () => {
  nextTick(() => {
    trendChartRef.value?.resize()
    rankChartRef.value?.resize()
  })
})

// 趋势图配置
const trendOptions = reactive({
  title: { text: '噪声小时趋势分析' },
  tooltip: { trigger: 'axis' },
  legend: { data: ['平均值', '最大值'] },
  xAxis: { type: 'category', data: [] },
  yAxis: { type: 'value', name: '分贝(dB)' },
  series: [
    { name: '平均值', type: 'line', data: [], smooth: true },
    { name: '最大值', type: 'line', data: [], smooth: true, lineStyle: { type: 'dashed' } }
  ]
})

// 排名图配置
const rankOptions = reactive({
  title: { text: '区域噪声排名 (Top 5)' },
  tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
  grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  xAxis: { type: 'value', boundaryGap: [0, 0.01] },
  yAxis: { type: 'category', data: [] },
  series: [
    { name: '平均噪声', type: 'bar', data: [], itemStyle: { color: '#409EFF' } }
  ]
})

// 合规率饼图
const pieOptions = reactive({
  title: { text: '噪声合规率分析', left: 'center' },
  tooltip: { trigger: 'item' },
  legend: { orient: 'vertical', left: 'left' },
  series: [
    {
      name: '统计',
      type: 'pie',
      radius: '50%',
      data: [],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }
  ]
})

// 构建日期参数
const buildDateParams = () => {
  if (analysisMode.value === 'daily' && selectedDate.value) {
    // 每日分析模式
    const date = selectedDate.value instanceof Date ? selectedDate.value : new Date(selectedDate.value)
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    const dateStr = `${year}-${month}-${day}`
    
    const startTimeStr = `${String(startHour.value).padStart(2, '0')}:00`
    const endTimeStr = `${String(endHour.value).padStart(2, '0')}:59`
    const startStr = `${dateStr}T${startTimeStr}:00`
    const endStr = `${dateStr}T${endTimeStr}:59`
    
    return `start_time=${encodeURIComponent(startStr)}&end_time=${encodeURIComponent(endStr)}`
  } else if (analysisMode.value === 'monthly' && selectedMonth.value) {
    // 月度分析模式
    const date = selectedMonth.value instanceof Date ? selectedMonth.value : new Date(selectedMonth.value)
    const year = date.getFullYear()
    const month = date.getMonth()
    const startDate = new Date(year, month, 1)
    const endDate = new Date(year, month + 1, 0, 23, 59, 59)
    
    const startStr = startDate.toISOString().split('.')[0]
    const endStr = endDate.toISOString().split('.')[0]
    
    return `start_time=${encodeURIComponent(startStr)}&end_time=${encodeURIComponent(endStr)}`
  }
  return ''
}

// 获取趋势数据
const fetchTrendData = async () => {
  try {
    const dateParams = buildDateParams()
    // 每日模式使用小时趋势，月度模式使用每日趋势
    const apiPath = analysisMode.value === 'daily' ? '/api/stats/hourly-trend' : '/api/stats/daily-stats'
    const url = dateParams ? `${apiPath}?${dateParams}` : apiPath
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data && data.length > 0) {
        if (analysisMode.value === 'daily') {
          // 每日模式：按小时显示
          trendOptions.title.text = '噪声小时趋势分析'
          trendOptions.xAxis.data = data.map((item, index) => 
            item.hour !== undefined ? `${String(item.hour).padStart(2, '0')}:00` : `${index}:00`
          )
        } else {
          // 月度模式：按日期显示
          trendOptions.title.text = '噪声每日趋势分析'
          trendOptions.xAxis.data = data.map(item => {
            if (item.date) {
              const d = new Date(item.date)
              return `${d.getMonth() + 1}/${d.getDate()}`
            }
            return item.day || ''
          })
        }
        trendOptions.series[0].data = data.map(item => Math.round((item.avg_db || item.avg || 0) * 10) / 10)
        trendOptions.series[1].data = data.map(item => Math.round((item.max_db || item.max || (item.avg_db || 0) + 10) * 10) / 10)
      } else {
        // 无数据时清空图表
        trendOptions.xAxis.data = []
        trendOptions.series[0].data = []
        trendOptions.series[1].data = []
      }
    }
  } catch (error) {
    console.error('获取趋势数据失败:', error)
  }
}

// 获取区域排名数据 (使用area-stats获取avg_db)
const fetchRankingData = async () => {
  try {
    // 尝试获取区域统计数据
    const dateParams = buildDateParams()
    const baseParams = 'limit=5'
    const params = dateParams ? `${baseParams}&${dateParams}` : baseParams
    const response = await fetch(`/api/stats/area-stats?${params}`, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      if (data && data.length > 0) {
        // 按avg_db排序取前5
        const sorted = data.filter(item => item.avg_db != null)
                          .sort((a, b) => (b.avg_db || 0) - (a.avg_db || 0))
                          .slice(0, 5)
        if (sorted.length > 0) {
          rankOptions.yAxis.data = sorted.map(item => item.area_name || item.name || '未知')
          rankOptions.series[0].data = sorted.map(item => Math.round((item.avg_db || 0) * 10) / 10)
        } else {
          // 无有效数据时清空
          rankOptions.yAxis.data = []
          rankOptions.series[0].data = []
        }
      } else {
        // 无数据时清空图表
        rankOptions.yAxis.data = []
        rankOptions.series[0].data = []
      }
    } else {
      // 回退到 area-ranking API
      const fallbackResponse = await fetch('/api/stats/area-ranking?limit=5', {
        headers: {
          'Authorization': `Bearer ${userStore.token}`
        }
      })
      if (fallbackResponse.ok) {
        const data = await fallbackResponse.json()
        if (data && data.length > 0) {
          rankOptions.yAxis.data = data.map(item => item.area_name || item.name || '未知')
          rankOptions.series[0].data = data.map(item => item.exceed_count || 0)
          rankOptions.series[0].name = '超标次数'
        }
      }
    }
  } catch (error) {
    console.error('获取排名数据失败:', error)
  }
}

// 获取概览数据用于饼图
const fetchOverviewData = async () => {
  try {
    const dateParams = buildDateParams()
    const url = dateParams ? `/api/stats/overview?${dateParams}` : '/api/stats/overview'
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${userStore.token}`
      }
    })
    if (response.ok) {
      const data = await response.json()
      // 检查是否有有效数据 (API返回today_readings)
      const readings = data.today_readings || data.total_readings || 0
      if (data && readings > 0) {
        const exceedRate = parseFloat(data.exceed_rate) || 0
        const complianceRate = 100 - exceedRate
        pieOptions.series[0].data = [
          { value: Math.round(complianceRate * 10) / 10, name: '达标', itemStyle: { color: '#67C23A' } },
          { value: Math.round(exceedRate * 10) / 10, name: '超标', itemStyle: { color: '#F56C6C' } }
        ]
      } else {
        // 无数据时清空饼图
        pieOptions.series[0].data = []
      }
    }
  } catch (error) {
    console.error('获取概览数据失败:', error)
  }
}

// 刷新所有数据
const refreshData = async () => {
  loading.value = true
  await Promise.all([
    fetchTrendData(),
    fetchRankingData(),
    fetchOverviewData()
  ])
  loading.value = false
  
  // 检查是否有数据，如果没有则提示
  // 检查是否有数据
  const hasDateSelected = analysisMode.value === 'daily' ? selectedDate.value : selectedMonth.value
  if (hasDateSelected && 
      trendOptions.xAxis.data.length === 0 && 
      rankOptions.yAxis.data.length === 0) {
    ElMessage.warning('所选日期范围内没有监测数据')
  }
}

// 导出报表
const handleExport = () => {
  ElMessage.info('导出功能开发中...')
}

onMounted(() => {
  refreshData()
})
</script>

<template>
  <div class="stats-container" v-loading="loading">
    <div class="toolbar">
      <span class="label">分析模式：</span>
      <el-radio-group v-model="analysisMode" @change="refreshData" size="small">
        <el-radio-button value="daily">每日分析</el-radio-button>
        <el-radio-button value="monthly">月度分析</el-radio-button>
      </el-radio-group>
      
      <!-- 每日分析模式 -->
      <template v-if="analysisMode === 'daily'">
        <span class="label" style="margin-left: 15px">统计日期：</span>
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          @change="refreshData"
          style="width: 150px"
        />
        <span class="label" style="margin-left: 15px">时间段：</span>
        <el-select v-model="startHour" style="width: 90px" @change="refreshData">
          <el-option
            v-for="item in hourOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
            :disabled="item.value > endHour"
          />
        </el-select>
        <span style="margin: 0 8px">至</span>
        <el-select v-model="endHour" style="width: 90px" @change="refreshData">
          <el-option
            v-for="item in hourOptions"
            :key="item.value"
            :label="item.label"
            :value="item.value"
            :disabled="item.value < startHour"
          />
        </el-select>
      </template>
      
      <!-- 月度分析模式 -->
      <template v-else>
        <span class="label" style="margin-left: 15px">统计月份：</span>
        <el-date-picker
          v-model="selectedMonth"
          type="month"
          placeholder="选择月份"
          @change="refreshData"
          style="width: 150px"
        />
      </template>
      
      <el-button :icon="Refresh" style="margin-left: 10px" @click="refreshData">刷新</el-button>
      <el-button type="primary" :icon="Download" style="margin-left: auto" @click="handleExport">导出报表</el-button>
    </div>

    <el-row :gutter="20" class="mt-20">
      <el-col :span="16">
        <el-card>
          <el-tabs v-model="activeTab">
            <el-tab-pane label="趋势分析" name="trend">
              <BaseChart ref="trendChartRef" :options="trendOptions" height="400px" />
            </el-tab-pane>
            <el-tab-pane label="区域对比" name="compare">
              <BaseChart ref="rankChartRef" :options="rankOptions" height="400px" />
            </el-tab-pane>
          </el-tabs>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card header="合规率概览">
          <BaseChart :options="pieOptions" height="400px" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.toolbar {
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  display: flex;
  align-items: center;
}
.label {
  margin-right: 10px;
  font-weight: bold;
}
.mt-20 {
  margin-top: 20px;
}
</style>
