-- =====================================================
-- 将数据更新为深圳市监测点
-- 运行方式: psql -h localhost -p 5432 -U postgres -d noise_db -f update_to_shenzhen.sql
-- =====================================================

-- 1. 清空相关数据（按依赖顺序）
TRUNCATE alerts CASCADE;
TRUNCATE noise_readings CASCADE;
TRUNCATE monitoring_points CASCADE;
TRUNCATE devices CASCADE;
TRUNCATE areas CASCADE;

-- 2. 插入深圳市区域
INSERT INTO areas (name, type, latitude, longitude) VALUES
    ('福田CBD商圈', 'commercial', 22.5333, 114.0545),
    ('南山科技园', 'commercial', 22.5362, 113.9300),
    ('罗湖住宅区', 'residential', 22.5488, 114.1315),
    ('宝安工业区', 'industrial', 22.5560, 113.8830),
    ('龙华交通枢纽', 'traffic', 22.6570, 114.0450);

-- 3. 插入设备
INSERT INTO devices (serial_no, model, installed_at, status) VALUES
    ('DEV-001', 'AWA5636', NOW() - INTERVAL '30 days', 'active'),
    ('DEV-002', 'AWA5636', NOW() - INTERVAL '25 days', 'active'),
    ('DEV-003', 'AWA6228', NOW() - INTERVAL '20 days', 'active'),
    ('DEV-004', 'AWA6228', NOW() - INTERVAL '15 days', 'active'),
    ('DEV-005', 'NL-52', NOW() - INTERVAL '10 days', 'active'),
    ('DEV-006', 'NL-52', NOW() - INTERVAL '5 days', 'maintenance'),
    ('DEV-007', 'AWA5636', NOW() - INTERVAL '8 days', 'active'),
    ('DEV-008', 'NL-52', NOW() - INTERVAL '3 days', 'active');

-- 4. 插入深圳市监测点
INSERT INTO monitoring_points (area_id, device_id, name, latitude, longitude, location_desc, threshold_db, status) VALUES
    ((SELECT id FROM areas WHERE name='福田CBD商圈'), 
     (SELECT id FROM devices WHERE serial_no='DEV-001'), 
     '福田中心区监测点', 22.5350, 114.0550, '福田CBD核心区域', 70.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='福田CBD商圈'), 
     (SELECT id FROM devices WHERE serial_no='DEV-002'), 
     '华强北商业街', 22.5470, 114.0880, '华强北步行街入口', 70.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='南山科技园'), 
     (SELECT id FROM devices WHERE serial_no='DEV-003'), 
     '南山软件产业基地', 22.5370, 113.9320, '科技园南区', 65.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='南山科技园'), 
     (SELECT id FROM devices WHERE serial_no='DEV-004'), 
     '深圳湾科技生态园', 22.5180, 113.9400, '深圳湾公园旁', 60.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='罗湖住宅区'), 
     (SELECT id FROM devices WHERE serial_no='DEV-005'), 
     '罗湖东门商圈', 22.5480, 114.1200, '东门步行街', 70.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='罗湖住宅区'), 
     NULL, 
     '罗湖住宅小区A', 22.5520, 114.1350, '翠竹路住宅区', 55.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='宝安工业区'), 
     (SELECT id FROM devices WHERE serial_no='DEV-006'), 
     '宝安机场周边', 22.6390, 113.8180, '机场T3航站楼', 75.00, 'active'),
    
    ((SELECT id FROM areas WHERE name='龙华交通枢纽'), 
     (SELECT id FROM devices WHERE serial_no='DEV-007'), 
     '深圳北站广场', 22.6100, 114.0300, '深圳北站东广场', 70.00, 'active');

-- 5. 插入阈值规则
DELETE FROM threshold_rules;
INSERT INTO threshold_rules (area_id, point_id, day_threshold, night_threshold, is_active) VALUES
    (NULL, NULL, 65.00, 55.00, TRUE),  -- 全局默认规则
    ((SELECT id FROM areas WHERE name='福田CBD商圈'), NULL, 70.00, 60.00, TRUE),
    ((SELECT id FROM areas WHERE name='南山科技园'), NULL, 65.00, 55.00, TRUE),
    ((SELECT id FROM areas WHERE name='罗湖住宅区'), NULL, 55.00, 45.00, TRUE),
    ((SELECT id FROM areas WHERE name='宝安工业区'), NULL, 75.00, 65.00, TRUE),
    ((SELECT id FROM areas WHERE name='龙华交通枢纽'), NULL, 70.00, 60.00, TRUE);

-- 6. 生成最近7天的模拟噪声数据
DO $$
DECLARE
    v_point_id INTEGER;
    v_day INTEGER;
    v_hour INTEGER;
    v_base_db NUMERIC;
    v_db_value NUMERIC;
    v_measured_at TIMESTAMPTZ;
    v_threshold NUMERIC;
BEGIN
    FOR v_point_id IN SELECT id FROM monitoring_points WHERE status = 'active' LOOP
        SELECT COALESCE(threshold_db, 65) INTO v_threshold 
        FROM monitoring_points WHERE id = v_point_id;
        
        v_base_db := v_threshold - 12;
        
        FOR v_day IN 0..6 LOOP
            FOR v_hour IN 0..23 LOOP
                FOR i IN 1..3 LOOP
                    v_measured_at := NOW() - (v_day || ' days')::INTERVAL 
                                   - (v_hour || ' hours')::INTERVAL 
                                   - ((i * 15) || ' minutes')::INTERVAL;
                    
                    v_db_value := v_base_db 
                                + (RANDOM() * 18) 
                                + CASE WHEN v_hour BETWEEN 7 AND 21 THEN 8 ELSE -3 END
                                + CASE WHEN RANDOM() > 0.85 THEN 12 ELSE 0 END;
                    
                    v_db_value := LEAST(GREATEST(v_db_value, 35), 90);
                    
                    INSERT INTO noise_readings (point_id, measured_at, db_value, temperature, humidity)
                    VALUES (
                        v_point_id,
                        v_measured_at,
                        ROUND(v_db_value::NUMERIC, 1),
                        ROUND((22 + RANDOM() * 12)::NUMERIC, 1),
                        ROUND((50 + RANDOM() * 35)::NUMERIC, 1)
                    );
                END LOOP;
            END LOOP;
        END LOOP;
    END LOOP;
    RAISE NOTICE '深圳市噪声数据生成完成';
END $$;

-- 7. 生成一些告警数据
DO $$
DECLARE
    v_point RECORD;
    v_reading RECORD;
    v_count INTEGER := 0;
BEGIN
    FOR v_point IN SELECT id, name, threshold_db FROM monitoring_points WHERE status = 'active' LOOP
        FOR v_reading IN 
            SELECT id, measured_at, db_value 
            FROM noise_readings 
            WHERE point_id = v_point.id 
              AND db_value > v_point.threshold_db
            ORDER BY RANDOM()
            LIMIT 3
        LOOP
            INSERT INTO alerts (point_id, reading_id, triggered_at, db_level, threshold, status, remark)
            VALUES (
                v_point.id,
                v_reading.id,
                v_reading.measured_at,
                v_reading.db_value,
                v_point.threshold_db,
                CASE WHEN RANDOM() > 0.4 THEN 'resolved' ELSE 'pending' END,
                CASE 
                    WHEN RANDOM() > 0.7 THEN '施工噪声'
                    WHEN RANDOM() > 0.4 THEN '交通高峰'
                    ELSE '商业活动'
                END
            );
            v_count := v_count + 1;
        END LOOP;
    END LOOP;
    RAISE NOTICE '生成告警数据 % 条', v_count;
END $$;

-- 8. 更新已解决的告警
UPDATE alerts 
SET resolved_at = triggered_at + INTERVAL '30 minutes',
    resolved_by = (SELECT id FROM users WHERE username = 'admin')
WHERE status = 'resolved';

-- 9. 统计信息
DO $$
DECLARE
    v_areas INTEGER;
    v_points INTEGER;
    v_readings INTEGER;
    v_alerts INTEGER;
    v_devices INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_areas FROM areas;
    SELECT COUNT(*) INTO v_points FROM monitoring_points;
    SELECT COUNT(*) INTO v_readings FROM noise_readings;
    SELECT COUNT(*) INTO v_alerts FROM alerts;
    SELECT COUNT(*) INTO v_devices FROM devices;
    
    RAISE NOTICE '====== 深圳市数据初始化完成 ======';
    RAISE NOTICE '区域数: %', v_areas;
    RAISE NOTICE '设备数: %', v_devices;
    RAISE NOTICE '监测点数: %', v_points;
    RAISE NOTICE '噪声数据条数: %', v_readings;
    RAISE NOTICE '告警数: %', v_alerts;
    RAISE NOTICE '================================';
END $$;
