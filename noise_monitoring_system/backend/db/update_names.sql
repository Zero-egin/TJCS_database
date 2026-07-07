-- 更新监测点名称为中文
UPDATE monitoring_points SET name = '福田中心区' WHERE id = 49;
UPDATE monitoring_points SET name = '华强北商业街' WHERE id = 50;
UPDATE monitoring_points SET name = '南山软件基地' WHERE id = 51;
UPDATE monitoring_points SET name = '深圳湾生态园' WHERE id = 52;
UPDATE monitoring_points SET name = '罗湖东门商圈' WHERE id = 53;
UPDATE monitoring_points SET name = '罗湖翠竹小区' WHERE id = 54;
UPDATE monitoring_points SET name = '宝安机场区域' WHERE id = 55;
UPDATE monitoring_points SET name = '深圳北站广场' WHERE id = 56;

-- 更新区域名称为中文
UPDATE areas SET name = '福田CBD商圈' WHERE name = 'Futian CBD';
UPDATE areas SET name = '南山科技园' WHERE name = 'Nanshan Tech Park';
UPDATE areas SET name = '罗湖住宅区' WHERE name = 'Luohu Residential';
UPDATE areas SET name = '宝安工业区' WHERE name = 'Baoan Industrial';
UPDATE areas SET name = '龙华交通枢纽' WHERE name = 'Longhua Transport Hub';
