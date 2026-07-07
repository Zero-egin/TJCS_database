-- =====================================================
-- 04_views.sql
-- 创建视图和持续聚合 (Continuous Aggregates)
-- =====================================================

-- TimescaleDB 持续聚合: 每日监测点统计
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_point_stats
WITH (timescaledb.continuous) AS
SELECT
    point_id,
    time_bucket('1 day', measured_at) AS day,
    COUNT(*) AS samples,
    AVG(db_value)::NUMERIC(5,2) AS avg_db,
    MIN(db_value) AS min_db,
    MAX(db_value) AS max_db,
    SUM(CASE WHEN is_exceed THEN 1 ELSE 0 END) AS exceed_count
FROM noise_readings
GROUP BY point_id, time_bucket('1 day', measured_at)
WITH NO DATA;

-- 创建刷新策略 (每小时自动刷新最近30天数据)
SELECT add_continuous_aggregate_policy(
    'mv_daily_point_stats',
    start_offset => INTERVAL '30 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 每日统计索引
CREATE INDEX IF NOT EXISTS idx_mv_daily_point_stats ON mv_daily_point_stats(point_id, day DESC);

-- TimescaleDB 持续聚合: 每小时区域统计
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hourly_area_stats
WITH (timescaledb.continuous) AS
SELECT
    mp.area_id,
    time_bucket('1 hour', nr.measured_at) AS hour,
    COUNT(*) AS samples,
    AVG(nr.db_value)::NUMERIC(5,2) AS avg_db,
    MAX(nr.db_value) AS max_db,
    SUM(CASE WHEN nr.is_exceed THEN 1 ELSE 0 END) AS exceed_count
FROM noise_readings nr
JOIN monitoring_points mp ON mp.id = nr.point_id
WHERE mp.area_id IS NOT NULL
GROUP BY mp.area_id, time_bucket('1 hour', nr.measured_at)
WITH NO DATA;

SELECT add_continuous_aggregate_policy(
    'mv_hourly_area_stats',
    start_offset => INTERVAL '7 days',
    end_offset   => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- 监测点地图视图 (包含最新噪声值)
CREATE OR REPLACE VIEW v_points_map AS
SELECT DISTINCT ON (mp.id)
    mp.id,
    mp.name,
    mp.latitude,
    mp.longitude,
    mp.threshold_db,
    mp.status AS point_status,
    a.id AS area_id,
    a.name AS area_name,
    a.type AS area_type,
    nr.db_value AS latest_db,
    nr.measured_at AS latest_time,
    nr.is_exceed,
    CASE 
        WHEN nr.db_value IS NULL THEN 'no_data'
        WHEN nr.is_exceed THEN 'exceed'
        ELSE 'normal'
    END AS status
FROM monitoring_points mp
LEFT JOIN areas a ON a.id = mp.area_id
LEFT JOIN noise_readings nr ON nr.point_id = mp.id
ORDER BY mp.id, nr.measured_at DESC NULLS LAST;

-- 告警详情视图
CREATE OR REPLACE VIEW v_alerts_detail AS
SELECT 
    al.id,
    al.reading_id,
    al.point_id,
    mp.name AS point_name,
    mp.latitude,
    mp.longitude,
    a.id AS area_id,
    a.name AS area_name,
    a.type AS area_type,
    al.type AS alert_type,
    al.severity,
    al.triggered_at,
    al.db_value,
    al.threshold_db,
    al.status,
    al.resolved_at,
    al.description,
    al.created_at
FROM alerts al
JOIN monitoring_points mp ON mp.id = al.point_id
LEFT JOIN areas a ON a.id = mp.area_id;
