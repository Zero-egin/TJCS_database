-- =====================================================
-- 02_functions.sql
-- 存储过程和触发器函数
-- =====================================================

-- 获取生效阈值 (优先级: 监测点 > 区域 > 默认)
CREATE OR REPLACE FUNCTION fn_effective_threshold(
    p_point_id INTEGER, 
    p_measured_at TIMESTAMPTZ
) RETURNS NUMERIC LANGUAGE plpgsql AS $$
DECLARE
    v_area_id INTEGER;
    v_hour INTEGER;
    v_thr NUMERIC(5,2);
    v_is_night BOOLEAN;
BEGIN
    v_hour := EXTRACT(HOUR FROM p_measured_at);
    -- 夜间定义: 22:00 - 06:00
    v_is_night := (v_hour >= 22 OR v_hour < 6);
    
    SELECT area_id INTO v_area_id FROM monitoring_points WHERE id = p_point_id;

    -- 查找监测点级别规则
    SELECT 
        CASE WHEN v_is_night THEN night_threshold ELSE day_threshold END 
    INTO v_thr
    FROM threshold_rules
    WHERE point_id = p_point_id AND is_active = TRUE
    LIMIT 1;
    
    IF v_thr IS NOT NULL THEN
        RETURN v_thr;
    END IF;

    -- 查找区域级别规则
    IF v_area_id IS NOT NULL THEN
        SELECT 
            CASE WHEN v_is_night THEN night_threshold ELSE day_threshold END 
        INTO v_thr
        FROM threshold_rules
        WHERE area_id = v_area_id AND point_id IS NULL AND is_active = TRUE
        LIMIT 1;
        
        IF v_thr IS NOT NULL THEN
            RETURN v_thr;
        END IF;
    END IF;

    -- 返回监测点默认阈值
    SELECT COALESCE(threshold_db, 65.00) INTO v_thr 
    FROM monitoring_points WHERE id = p_point_id;
    
    RETURN COALESCE(v_thr, 65.00);
END;
$$;

-- 计算超标状态的触发器函数
CREATE OR REPLACE FUNCTION fn_compute_is_exceed()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_thr NUMERIC(5,2);
BEGIN
    v_thr := fn_effective_threshold(NEW.point_id, NEW.measured_at);
    NEW.is_exceed := (NEW.db_value > v_thr);
    RETURN NEW;
END;
$$;

-- 超标时自动生成告警的触发器函数
CREATE OR REPLACE FUNCTION fn_alert_on_exceed()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_thr NUMERIC(5,2);
    v_diff NUMERIC(5,2);
    v_severity VARCHAR(20);
BEGIN
    v_thr := fn_effective_threshold(NEW.point_id, NEW.measured_at);
    
    IF NEW.db_value > v_thr THEN
        v_diff := NEW.db_value - v_thr;
        
        -- 根据超标程度确定严重级别
        IF v_diff >= 20 THEN
            v_severity := 'critical';
        ELSIF v_diff >= 10 THEN
            v_severity := 'high';
        ELSIF v_diff >= 5 THEN
            v_severity := 'medium';
        ELSE
            v_severity := 'low';
        END IF;
        
        INSERT INTO alerts(
            reading_id, point_id, type, severity, 
            triggered_at, db_value, threshold_db, status, description
        ) VALUES (
            NEW.id, NEW.point_id, 'threshold', v_severity,
            NEW.measured_at, NEW.db_value, v_thr, 'open',
            format('噪声值 %.2f dB 超过阈值 %.2f dB', NEW.db_value, v_thr)
        );
    END IF;
    
    RETURN NULL;
END;
$$;

-- 更新时间戳触发器函数
CREATE OR REPLACE FUNCTION fn_update_timestamp()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;
