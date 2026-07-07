<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  options: {
    type: Object,
    required: true
  },
  height: {
    type: String,
    default: '400px'
  }
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

const initChart = () => {
  if (chartRef.value) {
    // 如果容器宽度为0，延迟初始化
    if (chartRef.value.offsetWidth === 0) {
      return
    }
    if (chartInstance) {
      chartInstance.dispose()
    }
    chartInstance = echarts.init(chartRef.value)
    chartInstance.setOption(props.options)
  }
}

const resizeHandler = () => {
  if (chartInstance && chartRef.value && chartRef.value.offsetWidth > 0) {
    chartInstance.resize()
  }
}

// 使用 ResizeObserver 监听容器尺寸变化（处理 tab 切换等场景）
const setupResizeObserver = () => {
  if (chartRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
          if (!chartInstance) {
            initChart()
          } else {
            chartInstance.resize()
          }
        }
      }
    })
    resizeObserver.observe(chartRef.value)
  }
}

watch(() => props.options, (newOptions) => {
  if (chartInstance) {
    chartInstance.setOption(newOptions, { notMerge: false })
  } else if (chartRef.value && chartRef.value.offsetWidth > 0) {
    initChart()
  }
}, { deep: true })

onMounted(() => {
  nextTick(() => {
    initChart()
    setupResizeObserver()
  })
  window.addEventListener('resize', resizeHandler)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeHandler)
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  chartInstance?.dispose()
  chartInstance = null
})

// 暴露 resize 方法供父组件调用
defineExpose({
  resize: resizeHandler,
  refresh: initChart
})
</script>

<template>
  <div ref="chartRef" :style="{ height: height, width: '100%' }"></div>
</template>
