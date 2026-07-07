-- =====================================================
-- 00_extensions.sql
-- 启用必要的扩展 (TimescaleDB + PostGIS)
-- =====================================================

-- TimescaleDB 时序数据库扩展
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- PostGIS 空间数据库扩展
CREATE EXTENSION IF NOT EXISTS postgis;

-- 验证扩展安装
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB version: %', (SELECT extversion FROM pg_extension WHERE extname = 'timescaledb');
    RAISE NOTICE 'PostGIS version: %', (SELECT PostGIS_Version());
END $$;
