-- =====================================================
-- 01_tables.sql
-- 创建核心数据表
-- =====================================================

-- 角色表
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(200)
);

-- 用户表
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(120),
    phone VARCHAR(20),
    real_name VARCHAR(50),
    role_id INTEGER REFERENCES roles(id),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'locked', 'pending')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 区域表 (功能区)
CREATE TABLE areas (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    type VARCHAR(50) CHECK (type IN ('residential', 'commercial', 'industrial', 'traffic', 'special')),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    -- PostGIS 空间点 
    geom geometry(Point, 4326) GENERATED ALWAYS AS (
        CASE 
            WHEN latitude IS NOT NULL AND longitude IS NOT NULL 
            THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            ELSE NULL 
        END
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180)
);

-- 区域空间索引
CREATE INDEX IF NOT EXISTS idx_areas_geom ON areas USING GIST (geom);

-- 设备表
CREATE TABLE devices (
    id SERIAL PRIMARY KEY,
    serial_no VARCHAR(100) UNIQUE NOT NULL,
    model VARCHAR(100),
    installed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 监测点表
CREATE TABLE monitoring_points (
    id SERIAL PRIMARY KEY,
    area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    device_id INTEGER REFERENCES devices(id) ON DELETE SET NULL,
    name VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    -- PostGIS 空间点
    geom geometry(Point, 4326) GENERATED ALWAYS AS (
        CASE 
            WHEN latitude IS NOT NULL AND longitude IS NOT NULL 
            THEN ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
            ELSE NULL 
        END
    ) STORED,
    threshold_db NUMERIC(5,2) DEFAULT 65.00,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'maintenance')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (latitude IS NULL OR latitude BETWEEN -90 AND 90),
    CHECK (longitude IS NULL OR longitude BETWEEN -180 AND 180),
    CHECK (threshold_db BETWEEN 0 AND 200)
);

-- 监测点空间索引
CREATE INDEX IF NOT EXISTS idx_points_geom ON monitoring_points USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_points_area ON monitoring_points(area_id);

-- 噪声数据表 
CREATE TABLE noise_readings (
    id BIGSERIAL,
    point_id INTEGER NOT NULL REFERENCES monitoring_points(id) ON DELETE CASCADE,
    device_id INTEGER REFERENCES devices(id),
    measured_at TIMESTAMPTZ NOT NULL,
    db_value NUMERIC(5,2) NOT NULL,
    temperature NUMERIC(4,1),
    humidity NUMERIC(4,1),
    battery_pct NUMERIC(4,1),
    is_exceed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (id, measured_at),
    CHECK (db_value BETWEEN 0 AND 200)
);

-- TimescaleDB 超表 
SELECT create_hypertable('noise_readings', 'measured_at', if_not_exists => TRUE);

-- TimescaleDB 配置: 分块间隔、压缩、保留策略
SELECT set_chunk_time_interval('noise_readings', INTERVAL '7 days');
ALTER TABLE noise_readings SET (
    timescaledb.compress = true,
    timescaledb.compress_segmentby = 'point_id'
);
SELECT add_compression_policy('noise_readings', INTERVAL '30 days', if_not_exists => TRUE);
SELECT add_retention_policy('noise_readings', INTERVAL '24 months', if_not_exists => TRUE);

-- 噪声数据索引
CREATE INDEX IF NOT EXISTS idx_noise_readings_point_time ON noise_readings(point_id, measured_at DESC);
CREATE INDEX IF NOT EXISTS idx_noise_readings_exceed ON noise_readings(measured_at DESC) WHERE is_exceed = TRUE;

-- 告警表
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    reading_id BIGINT,
    point_id INTEGER NOT NULL REFERENCES monitoring_points(id) ON DELETE CASCADE,
    type VARCHAR(30) DEFAULT 'threshold' CHECK (type IN ('threshold', 'anomaly', 'trend')),
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    triggered_at TIMESTAMPTZ NOT NULL,
    db_value NUMERIC(5,2) NOT NULL,
    threshold_db NUMERIC(5,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved', 'dismissed')),
    resolved_at TIMESTAMPTZ,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alerts_point_time ON alerts(point_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alerts_open ON alerts(point_id, triggered_at) WHERE status = 'open';

-- 阈值规则表
CREATE TABLE threshold_rules (
    id SERIAL PRIMARY KEY,
    area_id INTEGER REFERENCES areas(id) ON DELETE SET NULL,
    point_id INTEGER REFERENCES monitoring_points(id) ON DELETE SET NULL,
    day_threshold NUMERIC(5,2) NOT NULL DEFAULT 65.00,
    night_threshold NUMERIC(5,2) NOT NULL DEFAULT 55.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CHECK (day_threshold BETWEEN 0 AND 200),
    CHECK (night_threshold BETWEEN 0 AND 200)
);

CREATE INDEX IF NOT EXISTS idx_threshold_rules_point ON threshold_rules(point_id) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_threshold_rules_area ON threshold_rules(area_id) WHERE is_active = TRUE;

-- 告警处理动作表
CREATE TABLE actions (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    action_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- 数据导入任务表
CREATE TABLE ingestion_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'success', 'failed')),
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    records_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 审计日志表
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id INTEGER,
    old_value JSONB,
    new_value JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id, created_at DESC);
