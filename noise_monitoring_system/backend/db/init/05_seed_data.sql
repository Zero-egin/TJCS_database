-- =====================================================
-- 05_seed_data.sql
-- 初始化种子数据
-- =====================================================

-- 插入角色 (三级权限体系)
-- super_admin: 超级管理员 - 系统运维与全局监管者
-- area_operator: 区域运维员 - 一线环境治理执行者  
-- public_user: 普通用户/市民 - 数据知情者与使用者
INSERT INTO roles (name, description) VALUES
    ('super_admin', '超级管理员：管理用户信息、配置区域阈值、审计系统日志、维护数据库完整性'),
    ('area_operator', '区域运维员：负责特定区域的数据导入(ETL)、处理报警记录、维护监测点设备状态'),
    ('public_user', '普通用户：查看噪声热力图、检索公开监测数据、查阅历史统计报表')
ON CONFLICT (name) DO NOTHING;

-- 插入默认超级管理员账户
-- 密码: admin123 (bcrypt hash)
INSERT INTO users (username, password_hash, email, role_id, status) VALUES
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S3VqNDGP9Xk1Ky', 'admin@noise.local', 
     (SELECT id FROM roles WHERE name = 'super_admin'), 'active')
ON CONFLICT (username) DO NOTHING;

-- 插入测试区域运维员账户
INSERT INTO users (username, password_hash, email, role_id, status) VALUES
    ('operator', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S3VqNDGP9Xk1Ky', 'operator@noise.local', 
     (SELECT id FROM roles WHERE name = 'area_operator'), 'active')
ON CONFLICT (username) DO NOTHING;

-- 插入测试普通用户账户
INSERT INTO users (username, password_hash, email, role_id, status) VALUES
    ('user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.S3VqNDGP9Xk1Ky', 'user@noise.local', 
     (SELECT id FROM roles WHERE name = 'public_user'), 'active')
ON CONFLICT (username) DO NOTHING;

-- 插入示例区域 (深圳市)
INSERT INTO areas (name, type, latitude, longitude) VALUES
    ('福田CBD商圈', 'commercial', 22.5333, 114.0545),
    ('南山科技园', 'commercial', 22.5362, 113.9300),
    ('罗湖住宅区', 'residential', 22.5488, 114.1315),
    ('宝安工业区', 'industrial', 22.5560, 113.8830),
    ('龙华交通枢纽', 'traffic', 22.6570, 114.0450)
ON CONFLICT DO NOTHING;

-- 插入示例设备
INSERT INTO devices (serial_no, model, installed_at, status) VALUES
    ('DEV-001', 'AWA5636', NOW() - INTERVAL '30 days', 'active'),
    ('DEV-002', 'AWA5636', NOW() - INTERVAL '25 days', 'active'),
    ('DEV-003', 'AWA6228', NOW() - INTERVAL '20 days', 'active'),
    ('DEV-004', 'AWA6228', NOW() - INTERVAL '15 days', 'active'),
    ('DEV-005', 'NL-52', NOW() - INTERVAL '10 days', 'active'),
    ('DEV-006', 'NL-52', NOW() - INTERVAL '5 days', 'maintenance'),
    ('DEV-007', 'AWA5636', NOW() - INTERVAL '8 days', 'active')
ON CONFLICT (serial_no) DO NOTHING;

-- 插入示例监测点 (深圳市)
INSERT INTO monitoring_points (area_id, device_id, name, latitude, longitude, location_desc, threshold_db, status) VALUES
    (1, 1, '福田中心区监测点', 22.5350, 114.0550, '福田CBD核心区域', 70.00, 'active'),
    (1, 2, '华强北商业街', 22.5470, 114.0880, '华强北步行街入口', 70.00, 'active'),
    (2, 3, '南山软件产业基地', 22.5370, 113.9320, '科技园南区', 65.00, 'active'),
    (2, 4, '深圳湾科技生态园', 22.5180, 113.9400, '深圳湾公园旁', 60.00, 'active'),
    (3, 5, '罗湖东门商圈', 22.5480, 114.1200, '东门步行街', 70.00, 'active'),
    (3, NULL, '罗湖住宅小区A', 22.5520, 114.1350, '翠竹路住宅区', 55.00, 'active'),
    (4, 6, '宝安机场周边', 22.6390, 113.8180, '机场T3航站楼', 75.00, 'active'),
    (5, 7, '深圳北站广场', 22.6100, 114.0300, '深圳北站东广场', 70.00, 'active')
ON CONFLICT DO NOTHING;

-- 插入示例阈值规则
INSERT INTO threshold_rules (area_id, point_id, day_threshold, night_threshold, is_active) VALUES
    -- 全局默认规则
    (NULL, NULL, 65.00, 55.00, TRUE),
    -- 商业区规则
    (1, NULL, 70.00, 60.00, TRUE),
    -- 住宅区规则
    (2, NULL, 55.00, 45.00, TRUE),
    -- 工业区规则
    (3, NULL, 75.00, 65.00, TRUE)
ON CONFLICT DO NOTHING;

-- 生成最近7天的模拟噪声数据
DO $$
DECLARE
    v_point_id INTEGER;
    v_day INTEGER;
    v_hour INTEGER;
    v_base_db NUMERIC;
    v_db_value NUMERIC;
    v_measured_at TIMESTAMPTZ;
BEGIN
    FOR v_point_id IN SELECT id FROM monitoring_points WHERE status = 'active' LOOP
        -- 获取该点位的基础噪声值
        SELECT COALESCE(threshold_db, 65) - 10 INTO v_base_db 
        FROM monitoring_points WHERE id = v_point_id;
        
        FOR v_day IN 0..6 LOOP
            FOR v_hour IN 0..23 LOOP
                -- 每小时2条数据
                FOR i IN 1..2 LOOP
                    v_measured_at := NOW() - (v_day || ' days')::INTERVAL 
                                   - (v_hour || ' hours')::INTERVAL 
                                   - ((i * 20) || ' minutes')::INTERVAL;
                    
                    -- 模拟噪声值: 基础值 + 随机波动 + 时段波动
                    v_db_value := v_base_db 
                                + (RANDOM() * 15) 
                                + CASE 
                                    WHEN v_hour BETWEEN 8 AND 20 THEN 10  -- 白天更吵
                                    ELSE 0 
                                  END
                                + CASE 
                                    WHEN RANDOM() > 0.9 THEN 15  -- 10%概率有噪声峰值
                                    ELSE 0 
                                  END;
                    
                    -- 限制范围
                    v_db_value := LEAST(GREATEST(v_db_value, 30), 95);
                    
                    INSERT INTO noise_readings (point_id, measured_at, db_value, temperature, humidity)
                    VALUES (
                        v_point_id,
                        v_measured_at,
                        ROUND(v_db_value::NUMERIC, 2),
                        ROUND((20 + RANDOM() * 15)::NUMERIC, 1),
                        ROUND((40 + RANDOM() * 40)::NUMERIC, 1)
                    )
                    ON CONFLICT DO NOTHING;
                END LOOP;
            END LOOP;
        END LOOP;
    END LOOP;
    
    RAISE NOTICE '模拟噪声数据生成完成';
END $$;

-- 手动刷新持续聚合视图
CALL refresh_continuous_aggregate('mv_daily_point_stats', NULL, NULL);

-- 统计信息
DO $$
DECLARE
    v_users INTEGER;
    v_points INTEGER;
    v_readings INTEGER;
    v_alerts INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_users FROM users;
    SELECT COUNT(*) INTO v_points FROM monitoring_points;
    SELECT COUNT(*) INTO v_readings FROM noise_readings;
    SELECT COUNT(*) INTO v_alerts FROM alerts;
    
    RAISE NOTICE '====== 数据库初始化完成 ======';
    RAISE NOTICE '用户数: %', v_users;
    RAISE NOTICE '监测点数: %', v_points;
    RAISE NOTICE '噪声数据条数: %', v_readings;
    RAISE NOTICE '告警数: %', v_alerts;
    RAISE NOTICE '================================';
END $$;
