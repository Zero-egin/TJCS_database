-- =====================================================
-- 03_triggers.sql
-- 创建触发器
-- =====================================================

-- 噪声数据插入/更新时计算超标状态
CREATE TRIGGER trg_noise_exceed_compute
BEFORE INSERT OR UPDATE ON noise_readings
FOR EACH ROW
EXECUTE FUNCTION fn_compute_is_exceed();

-- 噪声数据超标时自动生成告警
CREATE TRIGGER trg_noise_alert_after_insert
AFTER INSERT ON noise_readings
FOR EACH ROW
WHEN (NEW.is_exceed = TRUE)
EXECUTE FUNCTION fn_alert_on_exceed();

-- 用户表更新时间戳
CREATE TRIGGER trg_users_update_timestamp
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION fn_update_timestamp();
