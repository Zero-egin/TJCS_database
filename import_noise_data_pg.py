"""
大鹏新区噪声监测数据导入脚本 - PostgreSQL版本
目标数据库: Docker上运行的 TimescaleDB/PostgreSQL
使用conda虚拟环境: F:\miniconda3\envs\db_related\python.exe
"""
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime

# CSV文件路径
CSV_FILE = r'/path/to/your/data/noise_data.csv'  # 请根据实际情况修改路径

# PostgreSQL 数据库连接配置 (Docker)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres123',
    'database': 'noise_db'
}

# 站点信息映射 (通过高德地图查询大鹏新区的经纬度)
# 站点名称作为区域名称，站点编码作为监测点代码
STATION_INFO = {
    '葵涌文化广场': {
        'code': '2120106001',
        'lat': 22.629833,
        'lng': 114.413833,
        'threshold': 65.0,  # 商业/文化区域阈值
        'area_type': 'commercial',
    },
    '葵涌公园': {
        'code': '2120106002',
        'lat': 22.625833,
        'lng': 114.413500,
        'threshold': 60.0,  # 公园区域阈值稍低
        'area_type': 'special',
    },
    '大鹏广场': {
        'code': '2120206001',
        'lat': 22.590833,
        'lng': 114.478333,
        'threshold': 65.0,  # 商业广场阈值
        'area_type': 'commercial',
    },
    '万方广场': {
        'code': '2120206002',
        'lat': 22.626667,
        'lng': 114.414167,
        'threshold': 65.0,  # 商业广场阈值
        'area_type': 'commercial',
    }
}


def main():
    print("=" * 60)
    print("大鹏新区噪声监测数据导入工具 (PostgreSQL版)")
    print("=" * 60)
    
    # 1. 读取CSV文件
    print("\n[步骤1] 读取CSV文件...")
    try:
        # 尝试不同编码
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                df = pd.read_csv(CSV_FILE, encoding=encoding)
                print(f"  - 使用编码: {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        print(f"  - 数据总行数: {len(df)}")
        print(f"  - 数据列名: {list(df.columns)}")
        
        # 获取唯一站点
        stations = df[['站点编码', '站点名称']].drop_duplicates()
        print(f"  - 唯一站点数: {len(stations)}")
        for _, row in stations.iterrows():
            print(f"    · {row['站点编码']} - {row['站点名称']}")
    except Exception as e:
        print(f"读取CSV文件失败: {e}")
        return
    
    # 2. 连接数据库
    print("\n[步骤2] 连接PostgreSQL数据库...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        cursor = conn.cursor()
        # 验证连接
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  - 数据库连接成功!")
        print(f"  - PostgreSQL版本: {version[:50]}...")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        print("  请确保Docker容器正在运行: docker-compose up -d")
        return
    
    try:
        # 3. 创建区域 (areas表)
        print("\n[步骤3] 创建区域...")
        area_ids = {}  # 站点名称 -> area_id
        
        for station_name, info in STATION_INFO.items():
            # 检查区域是否已存在
            cursor.execute("SELECT id FROM areas WHERE name = %s", (station_name,))
            result = cursor.fetchone()
            
            if result:
                area_ids[station_name] = result[0]
                print(f"  - 区域已存在: {station_name} (id: {result[0]})")
            else:
                cursor.execute("""
                    INSERT INTO areas (name, type, latitude, longitude)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                """, (station_name, info['area_type'], info['lat'], info['lng']))
                area_id = cursor.fetchone()[0]
                area_ids[station_name] = area_id
                print(f"  - 创建新区域: {station_name} (id: {area_id})")
        
        # 4. 创建监测点 (monitoring_points表)
        print("\n[步骤4] 创建监测点...")
        point_ids = {}  # 站点编码 -> point_id
        
        for station_name, info in STATION_INFO.items():
            station_code = info['code']
            area_id = area_ids[station_name]
            
            # 检查监测点是否已存在 (通过名称匹配)
            cursor.execute("SELECT id FROM monitoring_points WHERE name = %s", (station_name,))
            result = cursor.fetchone()
            
            if result:
                point_ids[station_code] = result[0]
                print(f"  - 监测点已存在: {station_name} (id: {result[0]})")
            else:
                cursor.execute("""
                    INSERT INTO monitoring_points 
                    (area_id, name, latitude, longitude, threshold_db, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (area_id, station_name, info['lat'], info['lng'], 
                      info['threshold'], 'active'))
                point_id = cursor.fetchone()[0]
                point_ids[station_code] = point_id
                print(f"  - 创建新监测点: {station_name} (id: {point_id}, area_id: {area_id})")
        
        # 5. 构建阈值映射
        print("\n[步骤5] 获取监测点噪声阈值...")
        cursor.execute("""
            SELECT id, threshold_db FROM monitoring_points
        """)
        thresholds = {row[0]: float(row[1]) for row in cursor.fetchall()}
        print(f"  - 阈值映射: {thresholds}")
        
        # 6. 导入噪声数据
        print("\n[步骤6] 导入噪声数据...")
        
        # 检查已有数据量
        cursor.execute("SELECT COUNT(*) FROM noise_readings")
        existing_count = cursor.fetchone()[0]
        print(f"  - 数据库现有记录: {existing_count} 条")
        
        success_count = 0
        error_count = 0
        batch_size = 5000
        batch_data = []
        
        for idx, row in df.iterrows():
            try:
                station_code = str(int(row['站点编码']))
                station_name = row['站点名称']
                
                # 跳过未知站点
                if station_name not in STATION_INFO:
                    error_count += 1
                    continue
                
                # 跳过空值
                if pd.isna(row['监测时间']) or pd.isna(row['等效声级dB']) or pd.isna(row['站点编码']):
                    error_count += 1
                    continue
                
                point_id = point_ids.get(station_code)
                if not point_id:
                    error_count += 1
                    continue
                
                # 解析时间 (格式: 2025/1/15 14:00)
                measured_at = pd.to_datetime(row['监测时间'])
                db_value = float(row['等效声级dB'])
                
                # 计算是否超标
                threshold = thresholds.get(point_id, 65.0)
                is_exceed = db_value > threshold
                
                batch_data.append((
                    point_id,
                    measured_at,
                    db_value,
                    is_exceed
                ))
                
                # 批量插入
                if len(batch_data) >= batch_size:
                    execute_values(cursor, """
                        INSERT INTO noise_readings 
                        (point_id, measured_at, db_value, is_exceed)
                        VALUES %s
                    """, batch_data)
                    success_count += len(batch_data)
                    print(f"  - 已导入 {success_count} 条数据...")
                    batch_data = []
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:
                    print(f"  - 错误 (行{idx+2}): {e}")
        
        # 插入剩余数据
        if batch_data:
            execute_values(cursor, """
                INSERT INTO noise_readings 
                (point_id, measured_at, db_value, is_exceed)
                VALUES %s
            """, batch_data)
            success_count += len(batch_data)
        
        print(f"\n  ✓ 导入完成!")
        print(f"    - 成功: {success_count} 条")
        print(f"    - 失败/跳过: {error_count} 条")
        
        # 7. 统计信息
        print("\n[步骤7] 数据统计...")
        cursor.execute("SELECT COUNT(*) FROM noise_readings")
        total = cursor.fetchone()[0]
        print(f"  - 数据库总记录数: {total} 条")
        
        cursor.execute("""
            SELECT mp.name, 
                   COUNT(*) as cnt, 
                   MIN(nr.db_value) as min_val, 
                   MAX(nr.db_value) as max_val,
                   ROUND(AVG(nr.db_value)::numeric, 2) as avg_val,
                   SUM(CASE WHEN nr.is_exceed THEN 1 ELSE 0 END) as exceed_cnt
            FROM noise_readings nr
            JOIN monitoring_points mp ON nr.point_id = mp.id
            GROUP BY mp.id, mp.name
            ORDER BY cnt DESC
        """)
        
        print("\n  各站点数据统计:")
        print("  " + "-" * 70)
        print(f"  {'站点名称':<15} {'记录数':>8} {'最小值':>8} {'最大值':>8} {'平均值':>8} {'超标数':>8}")
        print("  " + "-" * 70)
        for row in cursor.fetchall():
            print(f"  {row[0]:<15} {row[1]:>8} {row[2]:>8.1f} {row[3]:>8.1f} {row[4]:>8.2f} {row[5]:>8}")
        print("  " + "-" * 70)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()
        print("\n数据库连接已关闭")
    
    print("\n" + "=" * 60)
    print("导入完成!")
    print("=" * 60)


if __name__ == '__main__':
    main()
