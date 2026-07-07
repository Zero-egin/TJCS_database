"""
区域数据访问层
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Area


class AreaRepository:
    """区域数据访问"""

    @staticmethod
    def get_by_id(db: Session, area_id: int) -> Optional[Area]:
        return db.get(Area, area_id)

    @staticmethod
    def get_all(db: Session) -> List[Area]:
        return db.query(Area).all()

    @staticmethod
    def get_by_type(db: Session, area_type: str) -> List[Area]:
        return db.query(Area).filter(Area.type == area_type).all()

    @staticmethod
    def create(db: Session, area: Area) -> Area:
        db.add(area)
        db.commit()
        db.refresh(area)
        return area

    @staticmethod
    def update(db: Session, area: Area) -> Area:
        db.commit()
        db.refresh(area)
        return area

    @staticmethod
    def delete(db: Session, area: Area) -> None:
        db.delete(area)
        db.commit()

    @staticmethod
    def count(db: Session) -> int:
        return db.query(Area).count()

    @staticmethod
    def get_exceed_ranking(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        limit: int = 10
    ) -> List[dict]:
        """
        获取超标重灾区排名 (基于 PostGIS 空间关联)
        统计各区域在指定时间段内的告警次数
        """
        sql = text("""
            SELECT 
                a.id AS area_id,
                a.name AS area_name,
                COUNT(al.id) AS exceed_count
            FROM areas a
            LEFT JOIN monitoring_points mp ON mp.area_id = a.id
            LEFT JOIN alerts al ON al.point_id = mp.id 
                AND al.triggered_at BETWEEN :start_time AND :end_time
            GROUP BY a.id, a.name
            ORDER BY exceed_count DESC
            LIMIT :limit
        """)
        result = db.execute(sql, {
            "start_time": start_time, 
            "end_time": end_time, 
            "limit": limit
        })
        return [
            {
                "area_id": row[0], 
                "area_name": row[1], 
                "exceed_count": row[2]
            } 
            for row in result
        ]

    @staticmethod
    def get_area_stats(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """
        获取各区域噪声统计
        """
        sql = text("""
            SELECT 
                a.id AS area_id,
                a.name AS area_name,
                AVG(nr.db_value) AS avg_db,
                MAX(nr.db_value) AS max_db,
                MIN(nr.db_value) AS min_db,
                COUNT(nr.id) AS sample_count,
                SUM(CASE WHEN nr.is_exceed THEN 1 ELSE 0 END) AS exceed_count
            FROM areas a
            LEFT JOIN monitoring_points mp ON mp.area_id = a.id
            LEFT JOIN noise_readings nr ON nr.point_id = mp.id 
                AND nr.measured_at BETWEEN :start_time AND :end_time
            GROUP BY a.id, a.name
            ORDER BY avg_db DESC NULLS LAST
        """)
        result = db.execute(sql, {
            "start_time": start_time, 
            "end_time": end_time
        })
        return [dict(row._mapping) for row in result]
