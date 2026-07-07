# 前端开发指南 (Vue 3 + Vite)

## 技术栈
- **核心框架**: Vue 3 (Composition API) + Vite
- **UI 组件库**: Element Plus (PC端管理后台风格)
- **图表库**: ECharts 5 (趋势图、饼图、仪表盘)
- **地图库**: Leaflet (轻量级 OSM 地图，支持热力图与点位聚合)
- **状态管理**: Pinia
- **路由**: Vue Router 4
- **HTTP 客户端**: Axios (封装拦截器与 JWT 认证)

## 目录结构
```
frontend/
├── public/              # 静态资源
├── src/
│   ├── api/             # API 接口定义 (auth, areas, points, stats, alerts)
│   ├── assets/          # 样式与图片
│   ├── components/      # 公共组件 (Map, Charts, Header)
│   ├── layouts/         # 布局组件 (Sidebar, Navbar)
│   ├── router/          # 路由配置
│   ├── stores/          # Pinia 状态管理 (user, app)
│   ├── views/           # 页面视图
│   │   ├── dashboard/   # 仪表盘 (统计图表 + 地图概览)
│   │   ├── monitor/     # 实时监测 (地图模式/列表模式)
│   │   ├── alerts/      # 报警管理 (列表与处置)
│   │   ├── admin/       # 系统管理 (用户、区域、设备)
│   │   └── login/       # 登录页
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── index.html           # HTML 模板
├── package.json         # 依赖配置
└── vite.config.js       # Vite 配置
```

## 核心功能页面
1. **登录页**: 用户名/密码登录，获取 JWT 存入 LocalStorage。
2. **仪表盘 (Dashboard)**:
   - 顶部：今日平均噪声、超标率、活跃设备数。
   - 中部：Leaflet 地图展示所有监测点（颜色区分状态：绿-正常，红-超标，灰-离线）。
   - 底部：ECharts 24小时噪声趋势图、区域噪声排名。
3. **实时监测 (Monitor)**:
   - 列表视图：分页展示监测点实时数据（支持按区域/状态筛选）。
   - 详情弹窗：点击点位查看该点历史曲线与阈值规则。
4. **报警管理 (Alerts)**:
   - 报警列表：按时间倒序，展示未处理告警。
   - 处置操作：点击“处置”弹出表单，填写备注并关闭告警。
5. **系统管理 (Admin)**:
   - 仅管理员可见。
   - 用户管理、区域绘制（地图打点）、设备录入。

## 开发步骤
1. 初始化项目：`npm create vite@latest frontend -- --template vue`
2. 安装依赖：
   ```bash
   npm install element-plus axios pinia vue-router echarts leaflet @types/leaflet
   npm install -D sass unplugin-vue-components unplugin-auto-import
   ```
3. 配置代理：在 `vite.config.js` 中设置 `/api` 代理到后端 `http://localhost:8000`。
