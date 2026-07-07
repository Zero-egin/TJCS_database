"""
监测点数据访问层
"""
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from app.models import MonitoringPoint, Area


class MonitoringPointRepository:
    """监测点数据访问"""

    @staticmethod
    def get_by_id(db: Session, point_id: int) -> Optional[MonitoringPoint]:
        return db.query(MonitoringPoint)\
            .options(joinedload(MonitoringPoint.area))\
            .filter(MonitoringPoint.id == point_id)\
            .first()

    @staticmethod
    def get_all(
        db: Session, 
        area_id: Optional[int] = None, 
        status: Optional[str] = None
    ) -> List[MonitoringPoint]:
        query = db.query(MonitoringPoint).options(joinedload(MonitoringPoint.area))
        if area_id:
            query = query.filter(MonitoringPoint.area_id == area_id)
        if status:
            query = query.filter(MonitoringPoint.status == status)
        return query.all()

    @staticmethod
    def create(db: Session, point: MonitoringPoint) -> MonitoringPoint:
        db.add(point)
        db.commit()
        db.refresh(point)
        return point

    @staticmethod
    def update(db: Session, point: MonitoringPoint) -> MonitoringPoint:
        db.commit()
        db.refresh(point)
        return point

    @staticmethod
    def delete(db: Session, point: MonitoringPoint) -> None:
        db.delete(point)
        db.commit()

    @staticmethod
    def count(db: Session) -> int:
        return db.query(MonitoringPoint).count()

    @staticmethod
    def count_active(db: Session) -> int:
        return db.query(MonitoringPoint).filter(MonitoringPoint.status == "active").count()

    @staticmethod
    def get_points_with_latest_reading(db: Session) -> List[dict]:
        """
        获取所有监测点及其最新一条噪声数据 (用于地图展示)
        使用 DISTINCT ON 确保每个监测点只返回一条最新记录
        """
        sql = text("""
            SELECT DISTINCT ON (mp.id)
                mp.id, 
                mp.name, 
                mp.latitude, 
                mp.longitude, 
                mp.threshold_db, 
                mp.status,
                a.name AS area_name, 
                a.type AS area_type,
                nr.db_value, 
                nr.measured_at, 
                nr.is_exceed
            FROM monitoring_points mp
            LEFT JOIN areas a ON a.id = mp.area_id
            LEFT JOIN noise_readings nr ON nr.point_id = mp.id
            ORDER BY mp.id, nr.measured_at DESC NULLS LAST
        """)
        result = db.execute(sql)
        return [dict(row._mapping) for row in result]

    @staticmethod
    def get_points_with_reading_at_time(
        db: Session, 
        reference_time: Optional[datetime] = None
    ) -> List[dict]:
        """
        获取所有监测点及其在指定时间附近的噪声数据 (用于历史回放)
        
        Args:
            db: 数据库会话
            reference_time: 参考时间点，如果不传则返回最新数据
        """
        if reference_time is None:
            # 如果没有指定时间，返回最新数据
            return MonitoringPointRepository.get_points_with_latest_reading(db)
        
        # 查询指定时间前后1小时内最接近的数据
        time_start = reference_time - timedelta(hours=1)
        time_end = reference_time + timedelta(hours=1)
        
        sql = text("""
            WITH ranked_readings AS (
                SELECT 
                    nr.point_id,
                    nr.db_value,
                    nr.measured_at,
                    nr.is_exceed,
                    ROW_NUMBER() OVER (
                        PARTITION BY nr.point_id 
                        ORDER BY ABS(EXTRACT(EPOCH FROM (nr.measured_at - :ref_time)))
                    ) AS rn
                FROM noise_readings nr
                WHERE nr.measured_at BETWEEN :time_start AND :time_end
            )
            SELECT 
                mp.id, 
                mp.name, 
                mp.latitude, 
                mp.longitude, 
                mp.threshold_db, 
                mp.status,
                a.name AS area_name, 
                a.type AS area_type,
                rr.db_value, 
                rr.measured_at, 
                rr.is_exceed
            FROM monitoring_points mp
            LEFT JOIN areas a ON a.id = mp.area_id
            LEFT JOIN ranked_readings rr ON rr.point_id = mp.id AND rr.rn = 1
            ORDER BY mp.id
        """)
        result = db.execute(sql, {
            "ref_time": reference_time,
            "time_start": time_start,
            "time_end": time_end
        })
        return [dict(row._mapping) for row in result]

    @staticmethod
    def get_points_by_area_type(db: Session, area_type: str) -> List[MonitoringPoint]:
        """根据区域类型获取监测点"""
        return db.query(MonitoringPoint)\
            .join(Area)\
            .filter(Area.type == area_type)\
            .options(joinedload(MonitoringPoint.area))\
            .all()

    @staticmethod
    def search_by_name(db: Session, name: str) -> List[MonitoringPoint]:
        """模糊搜索监测点名称"""
        return db.query(MonitoringPoint)\
            .options(joinedload(MonitoringPoint.area))\
            .filter(MonitoringPoint.name.ilike(f"%{name}%"))\
            .all()
