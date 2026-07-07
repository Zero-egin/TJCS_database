<script setup>
import { onMounted, ref, watch, onUnmounted } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

import icon from 'leaflet/dist/images/marker-icon.png'
import iconShadow from 'leaflet/dist/images/marker-shadow.png'

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
})
L.Marker.prototype.options.icon = DefaultIcon

const props = defineProps({
  center: {
    type: Array,
    default: () => [22.618800, 114.448996] // 默认深圳大鹏新区坐标
  },
  zoom: {
    type: Number,
    default: 13
  },
  points: {
    type: Array,
    default: () => []
  }
})

const mapContainer = ref(null)
let map = null
let markers = []

const initMap = () => {
  if (map) return
  if (!mapContainer.value) return

  // 确保坐标有效
  const center = (props.center && props.center[0] && props.center[1]) 
    ? props.center 
    : [22.5431, 114.0579]
  
  map = L.map(mapContainer.value).setView(center, props.zoom)

  // 使用 OpenStreetMap 图层
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }).addTo(map)
  
  updateMarkers()
}

const updateMarkers = () => {
  if (!map) return
  
  // 清除现有标记
  markers.forEach(marker => map.removeLayer(marker))
  markers = []
  
  props.points.forEach(point => {
    if (!point.lat || !point.lng) return

    const color = point.status === 'normal' ? '#67C23A' : (point.status === 'alarm' ? '#F56C6C' : '#909399')
    
    // 使用圆形标记，颜色代表状态
    const marker = L.circleMarker([point.lat, point.lng], {
      color: color,
      fillColor: color,
      fillOpacity: 0.6,
      radius: 12,
      weight: 2
    }).addTo(map)
    
    marker.bindPopup(`
      <div style="min-width: 150px">
        <h4 style="margin: 0 0 5px 0;">${point.name}</h4>
        <div><b>噪声值:</b> ${point.value} dB</div>
        <div><b>状态:</b> <span style="color:${color}">${point.status === 'normal' ? '正常' : (point.status === 'alarm' ? '超标' : '离线')}</span></div>
        <div style="margin-top: 5px; font-size: 12px; color: #666;">${point.address || '无详细地址'}</div>
      </div>
    `)
    
    markers.push(marker)
  })
}

watch(() => props.points, () => {
  updateMarkers()
}, { deep: true, immediate: true })

watch(() => props.center, (newCenter) => {
  if (map && newCenter && newCenter[0] && newCenter[1]) {
    map.setView(newCenter, map.getZoom())
  }
})

onMounted(() => {
  // 使用 setTimeout 确保在弹窗动画结束后初始化，避免容器高度为0导致地图显示异常
  setTimeout(() => {
    initMap()
    if (map) {
      map.invalidateSize()
    }
  }, 300)
  
  // 再次确保地图尺寸正确
  setTimeout(() => {
    if (map) {
      map.invalidateSize()
    }
  }, 1000)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<style scoped>
.map-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  z-index: 1;
}
</style>
