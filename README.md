# 城市声环境治理平台-23级同济计科数据库系统原理课程设计

基于 **PostgreSQL + TimescaleDB + PostGIS** 的全栈噪声监测与治理系统，支持实时噪声数据采集、超标自动报警、时空分析、地图可视化与系统管理。

## 技术栈

| 层级       | 技术                                          | 说明                                                 |
| ---------- | --------------------------------------------- | ---------------------------------------------------- |
| **数据库** | PostgreSQL 16 + TimescaleDB + PostGIS         | 时序超表、空间索引、连续聚合、压缩与保留策略         |
| **后端**   | FastAPI + SQLAlchemy 2.0 + GeoAlchemy2        | 三层架构（路由 → 服务 → 仓库），JWT 认证 + RBAC 权限 |
| **前端**   | Vue 3 (Composition API) + Vite + Element Plus | ECharts 5 图表、Leaflet 地图、Pinia 状态管理         |
| **容器**   | Docker Compose                                | PostgreSQL + pgAdmin 一键部署                        |

## 项目结构

```
homework/code/
├── import_noise_data_pg.py          # 批量导入 CSV 噪声数据的独立脚本
├── README.md
└── noise_monitoring_system/
    ├── backend/                     # FastAPI 后端
    │   ├── docker-compose.yml       # 数据库 + pgAdmin 容器编排
    │   ├── .env                     # 环境变量配置
    │   ├── requirements.txt         # Python 依赖
    │   ├── db/init/                 # 数据库初始化脚本
    │   │   ├── 00_extensions.sql    # TimescaleDB + PostGIS 扩展
    │   │   ├── 01_tables.sql        # 11 张核心表 + 超表/压缩/保留策略
    │   │   ├── 02_functions.sql     # PL/pgSQL 函数（阈值计算、超标判定）
    │   │   ├── 03_triggers.sql      # 自动超标检测 + 告警触发生成
    │   │   ├── 04_views.sql         # 连续聚合物化视图 + PostgreSQL 视图
    │   │   └── 05_seed_data.sql     # 种子数据 + 7 天模拟数据生成
    │   └── app/
    │       ├── main.py              # FastAPI 入口，CORS，路由注册
    │       ├── db.py                # SQLAlchemy 引擎与会话工厂
    │       ├── models.py            # 11 个 ORM 模型
    │       ├── core/                # 配置、安全（JWT/bcrypt）、依赖注入
    │       ├── schemas/             # Pydantic 请求/响应模型（10 个模块）
    │       ├── api/                 # API 路由（auth/points/readings/alerts/stats/admin）
    │       ├── services/            # 业务逻辑层（8 个服务模块）
    │       └── repositories/        # 数据访问层（9 个仓库模块）
    └── frontend/                    # Vue 3 前端
        ├── package.json             # 前端依赖
        ├── vite.config.js           # Vite 配置 + API 代理
        ├── dist/                    # 生产构建产物
        └── src/
            ├── main.js              # 应用入口
            ├── App.vue              # 根组件
            ├── router/index.js      # Vue Router 4 + 导航守卫
            ├── stores/user.js       # Pinia 状态管理（认证/角色/权限）
            ├── layouts/MainLayout.vue  # 主布局（侧边栏+面包屑+角色标签）
            ├── components/          # 通用组件
            │   ├── BaseMap.vue      # Leaflet 地图封装
            │   └── BaseChart.vue    # ECharts 图表封装
            └── views/               # 页面视图
                ├── login/           # 登录
                ├── register/        # 注册
                ├── dashboard/       # 仪表盘（统计卡片 + 24h 趋势图 + 区域排行）
                ├── monitor/         # 实时监测（地图 + 数据表格）
                ├── alerts/          # 报警管理（筛选/处理/归档/删除）
                ├── stats/           # 统计分析（区域对比/日趋势/严重性饼图）
                ├── data/            # 数据管理（CSV 导入/数据清洗）
                ├── admin/           # 系统管理（用户/区域/设备/监测点）
                ├── profile/         # 个人中心
                └── error/           # 403 / 404 错误页
```

## 功能特性

### 核心功能

- **实时监测** — 地图展示所有监测点，颜色编码（绿/红/灰）标识噪声状态，支持历史时刻回放
- **自动告警** — 数据库层触发器自动检测超标，按严重程度（低/中/高/严重）自动生成告警，支持昼夜双阈值
- **统计分析** — 仪表盘概览、区域噪声排名、24 小时趋势曲线、日统计报表
- **数据管理** — CSV 文件导入（支持 UTF-8/GBK/GB2312/GB18030 多编码）、导入任务追踪、历史数据清洗
- **系统管理** — 用户/区域/设备/监测点完整 CRUD，用户审批流程

### 认证与权限（RBAC）

| 角色                             | 权限                                     |
| -------------------------------- | ---------------------------------------- |
| **超级管理员** (`super_admin`)   | 全部权限，系统管理、用户审批、所有 CRUD  |
| **区域运维员** (`area_operator`) | 数据导入、告警处理、监测点管理、统计分析 |
| **普通用户** (`public_user`)     | 查看仪表盘、实时监测、统计分析、个人中心 |

系统定义了 11 种细粒度权限，前后端双重校验。

## 数据库设计

### 核心表（11 张）

| 表名                | 说明       | 亮点                                                         |
| ------------------- | ---------- | ------------------------------------------------------------ |
| `roles`             | 角色表     | —                                                            |
| `users`             | 用户表     | bcrypt 密码哈希                                              |
| `areas`             | 功能区表   | PostGIS 空间点（自动生成列）+ GIST 索引                      |
| `devices`           | 设备表     | 序列号唯一标识                                               |
| `monitoring_points` | 监测点表   | 空间索引 + 区域关联                                          |
| `noise_readings`    | 噪声读数表 | **TimescaleDB 超表**（7 天分块，30 天压缩，24 月保留）       |
| `alerts`            | 告警表     | 4 级严重度，状态流转（open→acknowledged→resolved/dismissed） |
| `threshold_rules`   | 阈值规则表 | 支持点级 > 区域级阈值层级，昼夜区分                          |
| `actions`           | 处理动作表 | 告警处理审计追踪                                             |
| `ingestion_jobs`    | 导入任务表 | CSV 导入状态与记录数追踪                                     |
| `audit_logs`        | 审计日志表 | JSONB 存储变更前后值                                         |

### 关键数据库特性

- **超表（Hypertable）**: `noise_readings` 按 7 天分块
- **压缩策略**: 30 天后自动压缩
- **保留策略**: 24 个月后自动删除
- **连续聚合**: `mv_daily_point_stats`、`mv_hourly_area_stats` 物化视图，自动刷新
- **空间索引**: `areas` 与 `monitoring_points` 使用 PostGIS GIST 索引
- **触发器**: 自动计算超标标记 → 自动生成告警

## 快速启动

### 前置条件

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Python 3.11+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)

### 1. 启动数据库

```bash
cd noise_monitoring_system/backend
docker compose up -d
```

启动后自动创建数据库并执行初始化脚本（扩展、表、函数、触发器、视图、种子数据）。

pgAdmin 管理界面访问 [http://localhost:5050](http://localhost:5050)：

- 邮箱: `admin@noise.local`
- 密码: `admin123`

### 2. 启动后端

```bash
cd noise_monitoring_system/backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动 FastAPI 服务 (端口 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

> 也可使用 conda 环境：`conda activate db_related`

API 文档访问 [http://localhost:8000/docs](http://localhost:8000/docs)。

### 3. 启动前端

```bash
cd noise_monitoring_system/frontend

# 安装依赖
npm install

# 启动开发服务器 (端口 5173)
npm run dev
```

前端代理已配置 `/api → localhost:8000`，可直接通过前端访问后端 API。

### 4. 访问系统

打开 [http://localhost:5173](http://localhost:5173)

**默认测试账号：**

| 角色       | 用户名     | 密码          |
| ---------- | ---------- | ------------- |
| 超级管理员 | `admin`    | `admin123`    |
| 区域运维员 | `operator` | `operator123` |
| 普通用户   | `user`     | `user123`     |

## 导入真实数据

项目附带了一个独立的批量导入脚本，用于将深圳大鹏新区的噪声监测 CSV 数据导入数据库：

```bash
# 确保数据库已启动，CSV 文件路径正确
python import_noise_data_pg.py
```

后端也支持通过 Web 界面上传 CSV 文件（数据管理页面），或通过 API 调用：

```bash
curl -X POST http://localhost:8000/api/readings/import \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv"
```

## API 概览

| 模块     | 端点                       | 方法         | 说明                   |
| -------- | -------------------------- | ------------ | ---------------------- |
| Auth     | `/api/auth/login`          | POST         | 登录获取 JWT           |
| Auth     | `/api/auth/register`       | POST         | 用户注册               |
| Auth     | `/api/auth/me`             | GET          | 当前用户信息           |
| Points   | `/api/points`              | GET          | 监测点列表             |
| Points   | `/api/points/map`          | GET          | 地图数据（含历史时刻） |
| Readings | `/api/readings`            | POST         | 提交噪声读数           |
| Readings | `/api/readings/trend`      | GET          | 趋势数据               |
| Readings | `/api/readings/timebucket` | GET          | TimescaleDB 时间桶聚合 |
| Readings | `/api/readings/import`     | POST         | CSV 导入               |
| Alerts   | `/api/alerts`              | GET          | 告警列表（分页+筛选）  |
| Alerts   | `/api/alerts/{id}/resolve` | POST         | 处理告警               |
| Stats    | `/api/stats/overview`      | GET          | 总览统计               |
| Stats    | `/api/stats/area-ranking`  | GET          | 区域排名               |
| Stats    | `/api/stats/hourly-trend`  | GET          | 24 小时趋势            |
| Admin    | `/api/admin/users`         | GET/POST/PUT | 用户管理               |
