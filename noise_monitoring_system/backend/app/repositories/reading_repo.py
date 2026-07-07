"""
噪声数据访问层 (TimescaleDB)
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models import NoiseReading


class NoiseReadingRepository:
    """噪声数据访问 (TimescaleDB)"""

    @staticmethod
    def get_time_range(db: Session) -> dict:
        """获取数据库中噪声数据的时间范围"""
        result = db.query(
            func.min(NoiseReading.measured_at),
            func.max(NoiseReading.measured_at)
        ).first()
        return {
            'min_time': result[0] if result else None,
            'max_time': result[1] if result else None
        }

    @staticmethod
    def get_avg_for_period(db: Session, start_time: datetime, end_time: datetime) -> Decimal:
        """获取指定时间段的平均噪声"""
        result = db.query(func.avg(NoiseReading.db_value)).filter(
            NoiseReading.measured_at >= start_time,
            NoiseReading.measured_at < end_time
        ).scalar()
        return round(result, 2) if result else Decimal("0")

    @staticmethod
    def get_count_for_period(db: Session, start_time: datetime, end_time: datetime) -> int:
        """获取指定时间段的采样数"""
        return db.query(NoiseReading).filter(
            NoiseReading.measured_at >= start_time,
            NoiseReading.measured_at < end_time
        ).count()

    @staticmethod
    def create(db: Session, reading: NoiseReading) -> NoiseReading:
        db.add(reading)
        db.commit()
        db.refresh(reading)
        return reading

    @staticmethod
    def bulk_create(db: Session, readings: List[NoiseReading]) -> int:
        """批量创建噪声数据"""
        if not readings:
            return 0
        try:
            db.bulk_save_objects(readings)
            db.commit()
            return len(readings)
        except Exception as e:
            db.rollback()
            print(f"[bulk_create] 批量插入失败: {e}")
            # 尝试逐条插入，跳过失败的记录
            success_count = 0
            for reading in readings:
                try:
                    db.add(reading)
                    db.commit()
                    success_count += 1
                except Exception as inner_e:
                    db.rollback()
                    print(f"[bulk_create] 单条插入失败 point_id={reading.point_id}: {inner_e}")
            return success_count

    @staticmethod
    def get_by_point_and_time(
        db: Session, 
        point_id: int, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[NoiseReading]:
        """获取指定监测点在时间范围内的数据"""
        return db.query(NoiseReading).filter(
            NoiseReading.point_id == point_id,
            NoiseReading.measured_at >= start_time,
            NoiseReading.measured_at <= end_time
        ).order_by(NoiseReading.measured_at).all()

    @staticmethod
    def get_hourly_trend(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        point_id: Optional[int] = None
    ) -> List[dict]:
        """
        使用 TimescaleDB time_bucket 获取小时聚合趋势
        """
        point_filter = "AND point_id = :point_id" if point_id else ""
        sql = text(f"""
            SELECT 
                EXTRACT(HOUR FROM time_bucket('1 hour', measured_at)) AS hour,
                AVG(db_value) AS avg_db,
                MAX(db_value) AS max_db,
                MIN(db_value) AS min_db
            FROM noise_readings
            WHERE measured_at BETWEEN :start_time AND :end_time {point_filter}
            GROUP BY hour
            ORDER BY hour
        """)
        params = {"start_time": start_time, "end_time": end_time}
        if point_id:
            params["point_id"] = point_id
        result = db.execute(sql, params)
        return [
            {
                "hour": int(row[0]), 
                "avg_db": round(row[1], 2),
                "max_db": round(row[2], 2) if row[2] else None,
                "min_db": round(row[3], 2) if row[3] else None
            } 
            for row in result
        ]

    @staticmethod
    def get_time_bucket_data(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        bucket_interval: str = "1 hour"
    ) -> List[dict]:
        """
        获取指定时间桶聚合数据 (用于时间轴播放)
        """
        sql = text(f"""
            SELECT 
                time_bucket(:interval, measured_at) AS bucket,
                point_id,
                AVG(db_value) AS avg_db,
                MAX(db_value) AS max_db,
                MIN(db_value) AS min_db,
                SUM(CASE WHEN is_exceed THEN 1 ELSE 0 END) AS exceed_count,
                COUNT(*) AS sample_count
            FROM noise_readings
            WHERE measured_at BETWEEN :start_time AND :end_time
            GROUP BY bucket, point_id
            ORDER BY bucket, point_id
        """)
        result = db.execute(sql, {
            "interval": bucket_interval,
            "start_time": start_time,
            "end_time": end_time
        })
        return [dict(row._mapping) for row in result]

    @staticmethod
    def get_today_avg(db: Session) -> Decimal:
        """获取今日全市平均噪声"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = db.query(func.avg(NoiseReading.db_value)).filter(
            NoiseReading.measured_at >= today
        ).scalar()
        return round(result, 2) if result else Decimal("0")

    @staticmethod
    def get_today_count(db: Session) -> int:
        """获取今日采样数"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return db.query(NoiseReading).filter(
            NoiseReading.measured_at >= today
        ).count()

    @staticmethod
    def get_daily_stats(
        db: Session, 
        start_time: datetime, 
        end_time: datetime,
        area_id: Optional[int] = None
    ) -> List[dict]:
        """
        获取每日统计数据
        """
        area_filter = """
            AND mp.area_id = :area_id
        """ if area_id else ""
        
        sql = text(f"""
            SELECT 
                DATE(nr.measured_at) AS date,
                AVG(nr.db_value) AS avg_db,
                MAX(nr.db_value) AS max_db,
                MIN(nr.db_value) AS min_db,
                SUM(CASE WHEN nr.is_exceed THEN 1 ELSE 0 END) AS exceed_count,
                COUNT(*) AS sample_count
            FROM noise_readings nr
            JOIN monitoring_points mp ON mp.id = nr.point_id
            WHERE nr.measured_at BETWEEN :start_time AND :end_time
            {area_filter}
            GROUP BY DATE(nr.measured_at)
            ORDER BY date
        """)
        params = {"start_time": start_time, "end_time": end_time}
        if area_id:
            params["area_id"] = area_id
        result = db.execute(sql, params)
        return [dict(row._mapping) for row in result]

    @staticmethod
    def get_exceed_rate(db: Session, start_time: datetime, end_time: datetime) -> Decimal:
        """计算超标率"""
        total = db.query(NoiseReading).filter(
            NoiseReading.measured_at >= start_time,
            NoiseReading.measured_at <= end_time
        ).count()
        
        if total == 0:
            return Decimal("0")
        
        exceed = db.query(NoiseReading).filter(
            NoiseReading.measured_at >= start_time,
            NoiseReading.measured_at <= end_time,
            NoiseReading.is_exceed == True
        ).count()
        
        return round(Decimal(exceed) / Decimal(total) * 100, 2)
