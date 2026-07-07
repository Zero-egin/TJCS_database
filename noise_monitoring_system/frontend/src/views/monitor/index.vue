<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BaseMap from '@/components/BaseMap.vue'
import { Search, Refresh, VideoPlay, VideoPause, Trophy, Calendar } from '@element-plus/icons-vue'

const loading = ref(false)

// 数据时间范围
const dataRange = ref({
  min: null,
  max: null
})

// 当前选择的日期
const selectedDate = ref(null)

// 历史数据时间点 (24小时) - 直接初始化避免空数组问题
const timeSteps = ref([
  '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
  '06:00', '07:00', '08:00', '09:00', '10:00', '11:00',
  '12:00', '13:00', '14:00', '15:00', '16:00', '17:00',
  '18:00', '19:00', '20:00', '21:00', '22:00', '23:00'
])
const currentTimeIndex = ref(12) // 默认中午12点
const isPlaying = ref(false)
let playTimer = null

// 从后端获取的点位数据
const rawPoints = ref([])

// 区域排名
const areaRankings = ref([])

// 获取数据时间范围
const fetchDataRange = async () => {
  try {
    const response = await fetch('/api/stats/data-range')
    if (response.ok) {
      const data = await response.json()
      console.log('Data range:', data)
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

// 获取监测点数据（支持历史时间查询）
const fetchPoints = async () => {
  try {
    loading.value = true
    
    // 构建时间参数
    let url = '/api/points/map'
    if (selectedDate.value) {
      const queryDate = new Date(selectedDate.value)
      const hour = parseInt(timeSteps.value[currentTimeIndex.value])
      queryDate.setHours(hour, 0, 0, 0)
      url += `?reference_time=${encodeURIComponent(queryDate.toISOString())}`
    }
    
    const response = await fetch(url)
    console.log('API Response status:', response.status)
    if (response.ok) {
      const data = await response.json()
      console.log('Fetched points:', data.length)
      rawPoints.value = data.map(p => ({
        id: p.id,
        name: p.name,
        lat: p.latitude,
        lng: p.longitude,
        address: p.area_name || '',
        value: p.db_value || 0,
        status: getStatus(p.db_value || 0, p.status)
      }))
    } else {
      console.error('API error:', response.status, await response.text())
    }
  } catch (error) {
    console.error('获取监测点数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取区域超标排名
const fetchAreaRanking = async () => {
  try {
    let url = '/api/stats/area-ranking?limit=5'
    if (selectedDate.value) {
      const endDate = new Date(selectedDate.value)
      endDate.setHours(23, 59, 59, 999)
      const startDate = new Date(selectedDate.value)
      startDate.setDate(startDate.getDate() - 30)
      url += `&start_time=${startDate.toISOString()}&end_time=${endDate.toISOString()}`
    }
    const response = await fetch(url)
    if (response.ok) {
      const data = await response.json()
      areaRankings.value = data.map(item => ({
        name: item.area_name || item.name || '未知区域',
        count: item.exceed_count || item.alert_count || 0
      })).sort((a, b) => b.count - a.count)
    }
  } catch (error) {
    console.error('获取区域排名失败:', error)
  }
}

const getStatus = (val, deviceStatus) => {
  if (deviceStatus === 'inactive' || deviceStatus === 'offline') return 'offline'
  if (val > 65) return 'alarm'
  if (val > 0) return 'normal'
  return 'offline'
}

// 计算当前展示的点位 (支持筛选)
const currentPoints = computed(() => {
  let points = rawPoints.value
  if (filters.value.keyword) {
    const kw = filters.value.keyword.toLowerCase()
    points = points.filter(p => 
      p.name.toLowerCase().includes(kw) || 
      (p.address && p.address.toLowerCase().includes(kw))
    )
  }
  if (filters.value.status) {
    points = points.filter(p => p.status === filters.value.status)
  }
  return points
})

const togglePlay = () => {
  if (isPlaying.value) {
    clearInterval(playTimer)
    isPlaying.value = false
  } else {
    isPlaying.value = true
    playTimer = setInterval(() => {
      if (currentTimeIndex.value < timeSteps.value.length - 1) {
        currentTimeIndex.value++
      } else {
        currentTimeIndex.value = 0 // 循环播放
      }
      // 刷新数据
      fetchPoints()
    }, 2000)
  }
}

const handleSliderChange = (val) => {
  // 拖动滑块时暂停播放
  if (isPlaying.value) {
    togglePlay()
  }
  fetchPoints()
}

const handleRefresh = () => {
  fetchPoints()
  fetchAreaRanking()
}

// 日期改变时重新获取数据
const handleDateChange = () => {
  currentTimeIndex.value = 12 // 默认中午12点
  fetchPoints()
  fetchAreaRanking()
}

// 禁用超出数据范围的日期（已禁用限制，允许选择任意日期）
const disabledDate = (date) => {
  // 不再限制日期范围，允许选择任意日期
  // 如果选择的日期没有数据，地图将显示空或离线状态
  return false
}

// 格式化日期范围显示
const formatDateRange = () => {
  if (!dataRange.value.min || !dataRange.value.max) return '加载中...'
  const min = dataRange.value.min.toLocaleDateString('zh-CN')
  const max = dataRange.value.max.toLocaleDateString('zh-CN')
  return `${min} ~ ${max}`
}

// 获取当前显示的日期时间
const currentDateTime = computed(() => {
  if (!selectedDate.value) return ''
  const d = new Date(selectedDate.value)
  return `${d.toLocaleDateString('zh-CN')} ${timeSteps.value[currentTimeIndex.value]}`
})

onMounted(async () => {
  await fetchDataRange()
  fetchPoints()
  fetchAreaRanking()
})

onUnmounted(() => {
  clearInterval(playTimer)
})

const filters = ref({
  keyword: '',
  status: ''
})

const handleSearch = () => {
  // 筛选已通过computed实现
}
</script>

<template>
  <div class="monitor-container">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="left">
        <el-date-picker
          v-model="selectedDate"
          type="date"
          placeholder="选择日期"
          :disabled-date="disabledDate"
          @change="handleDateChange"
          style="width: 150px"
        />
        <el-input
          v-model="filters.keyword"
          placeholder="搜索监测点名称/地址"
          style="width: 200px; margin-left: 10px"
          :prefix-icon="Search"
          clearable
        />
        <el-select v-model="filters.status" placeholder="状态筛选" style="width: 120px; margin-left: 10px" clearable>
          <el-option label="正常" value="normal" />
          <el-option label="超标" value="alarm" />
          <el-option label="离线" value="offline" />
        </el-select>
        <el-button type="primary" style="margin-left: 10px" @click="handleSearch">查询</el-button>
      </div>
      <div class="center">
        <el-tag type="info" size="large">
          数据范围: {{ formatDateRange() }}
        </el-tag>
      </div>
      <div class="right">
        <el-button :icon="Refresh" circle @click="handleRefresh" :loading="loading" />
      </div>
    </div>

    <div class="content-wrapper">
      <el-card class="map-card" v-loading="loading">
        <div class="map-wrapper">
          <BaseMap :points="currentPoints" />
        </div>
        
        <!-- 当前时间显示 -->
        <div class="current-time-display">
          <el-icon><Calendar /></el-icon>
          <span>{{ currentDateTime }}</span>
        </div>
        
        <!-- 历史回溯播放条 (悬浮) -->
        <div class="playback-control">
          <div class="control-btn" @click="togglePlay">
            <el-icon :size="24" color="#409EFF">
              <VideoPause v-if="isPlaying" />
              <VideoPlay v-else />
            </el-icon>
          </div>
          <div class="slider-area">
            <span class="time-label">{{ timeSteps[currentTimeIndex] }}</span>
            <el-slider 
              v-model="currentTimeIndex" 
              :min="0" 
              :max="timeSteps.length - 1" 
              :step="1"
              :show-tooltip="false"
              @change="handleSliderChange"
            />
          </div>
        </div>

        <!-- 区域超标排名 (悬浮) -->
        <div class="ranking-panel">
          <div class="panel-header">
            <el-icon><Trophy /></el-icon>
            <span>超标重灾区排名</span>
          </div>
          <div class="panel-body">
            <div v-for="(item, index) in areaRankings" :key="index" class="rank-item">
              <span class="rank-num" :class="'top-' + (index + 1)">{{ index + 1 }}</span>
              <span class="area-name">{{ item.name }}</span>
              <span class="count-tag">{{ item.count }}次</span>
            </div>
            <el-empty v-if="areaRankings.length === 0" description="暂无数据" :image-size="60" />
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<style scoped>
.monitor-container {
  height: 100%;
  min-height: 600px;
  display: flex;
  flex-direction: column;
}

.toolbar {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  padding: 15px;
  border-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,21,41,.08);
}

.toolbar .center {
  flex: 1;
  text-align: center;
}

.content-wrapper {
  flex: 1;
  min-height: 500px;
}

.map-card {
  height: 100%;
  min-height: 500px;
  border: none;
}

.map-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
  position: relative;
}

.map-wrapper {
  width: 100%;
  height: 100%;
  min-height: 500px;
}

/* 当前时间显示 */
.current-time-display {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(64, 158, 255, 0.9);
  color: white;
  padding: 10px 25px;
  border-radius: 25px;
  font-size: 16px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 10px;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

/* 播放条样式 */
.playback-control {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%);
  width: 60%;
  background: rgba(255, 255, 255, 0.95);
  padding: 10px 20px;
  border-radius: 30px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  display: flex;
  align-items: center;
  gap: 15px;
  z-index: 1000; /* 确保在地图之上 */
}

.control-btn {
  cursor: pointer;
  display: flex;
  align-items: center;
}

.slider-area {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.time-label {
  font-weight: bold;
  color: #303133;
  min-width: 50px;
}

/* 排名面板样式 */
.ranking-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 220px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  overflow: hidden;
}

.panel-header {
  background: #409EFF;
  color: #fff;
  padding: 10px 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
}

.panel-body {
  padding: 10px;
  max-height: 250px;
  overflow-y: auto;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.rank-item:last-child {
  border-bottom: none;
}

.rank-num {
  width: 20px;
  height: 20px;
  line-height: 20px;
  text-align: center;
  border-radius: 50%;
  background: #909399;
  color: #fff;
  font-size: 12px;
  margin-right: 10px;
}

.rank-num.top-1 { background: #F56C6C; }
.rank-num.top-2 { background: #E6A23C; }
.rank-num.top-3 { background: #E6A23C; }

.area-name {
  flex: 1;
  font-size: 14px;
}

.count-tag {
  font-size: 12px;
  color: #F56C6C;
  font-weight: bold;
}
</style>
