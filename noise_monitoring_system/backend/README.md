# 城市声环境治理平台 - 后端

## 数据库搭建 (Docker)

### 前置条件

1. **安装 Docker Desktop**
   - Windows: https://www.docker.com/products/docker-desktop/
   - 安装后确保 Docker 正在运行

2. **验证 Docker 安装**
   ```powershell
   docker --version
   docker-compose --version
   ```

### 启动数据库

```powershell
# 进入后端目录
cd noise_monitoring_system/backend

# 启动数据库容器 (首次会自动下载镜像)
docker-compose up -d

# 查看容器状态
docker-compose ps

# 查看数据库日志
docker-compose logs -f db
```

### 数据库信息

| 项目 | 值 |
|------|-----|
| 主机 | localhost |
| 端口 | 5432 |
| 数据库 | noise_db |
| 用户名 | postgres |
| 密码 | postgres123 |
| 连接串 | postgresql://postgres:postgres123@localhost:5432/noise_db |

### pgAdmin 访问 (可选)

- 地址: http://localhost:5050
- 邮箱: admin@noise.local
- 密码: admin123

### 常用命令

```powershell
# 停止容器
docker-compose down

# 停止并删除数据卷 (清空数据库)
docker-compose down -v

# 重新初始化数据库
docker-compose down -v
docker-compose up -d

# 进入数据库容器
docker exec -it noise_db psql -U postgres -d noise_db

# 查看数据库表
docker exec -it noise_db psql -U postgres -d noise_db -c "\dt"

# 查看扩展
docker exec -it noise_db psql -U postgres -d noise_db -c "\dx"
```

---

## Python 环境搭建

### 1. 配置环境

本项目使用已有的 Conda 虚拟环境 `db_related`。

```powershell
# 进入后端目录
cd noise_monitoring_system/backend

# 激活 Conda 环境
conda activate db_related

# Python 解释器路径: F:\miniconda3\envs\db_related\python.exe
```

### 2. 安装依赖

```powershell
# 确保已激活虚拟环境
pip install -r requirements.txt
```

### 3. 配置环境变量

```powershell
# 复制环境变量模板 (已自动创建 .env)
copy .env.example .env

# 编辑 .env 文件 (可选，默认配置已可用)
```

---

## 启动应用

### 1. 确保数据库已启动

```powershell
docker-compose ps
# 应显示 noise_db 状态为 running (healthy)
```

### 2. 启动 FastAPI 服务

```powershell
# 激活 Conda 环境
conda activate db_related

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问 API

- API 文档: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

---

## 默认账户

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |

---

## 项目结构

```
backend/
 app/
    api/           # API 路由
    core/          # 核心配置
    models.py      # ORM 模型
    repositories/  # 数据访问层
    schemas/       # Pydantic 模型
    services/      # 业务逻辑层
    db.py          # 数据库连接
    main.py        # FastAPI 入口
 db/
    init/          # 数据库初始化脚本
       00_extensions.sql
       01_tables.sql
       02_functions.sql
       03_triggers.sql
       04_views.sql
       05_seed_data.sql
    schema.sql     # 完整 Schema (参考)
 docker-compose.yml # Docker 编排配置
 requirements.txt   # Python 依赖
 .env              # 环境变量
 .env.example      # 环境变量模板
```

---

## 技术栈

- **数据库**: PostgreSQL 16 + TimescaleDB + PostGIS
- **后端框架**: FastAPI + SQLAlchemy 2.0
- **认证**: JWT (python-jose)
- **容器**: Docker + Docker Compose
