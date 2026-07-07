"""
区域管理服务
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Area
from app.repositories import AreaRepository
from app.schemas import AreaCreate


class AreaService:
    """区域管理服务"""

    @staticmethod
    def create_area(db: Session, data: AreaCreate) -> Area:
        """创建区域"""
        area = Area(
            name=data.name,
            type=data.type,
            latitude=data.latitude,
            longitude=data.longitude
        )
        return AreaRepository.create(db, area)

    @staticmethod
    def get_area(db: Session, area_id: int) -> Optional[Area]:
        """获取区域"""
        return AreaRepository.get_by_id(db, area_id)

    @staticmethod
    def get_all_areas(db: Session) -> List[Area]:
        """获取所有区域"""
        return AreaRepository.get_all(db)

    @staticmethod
    def get_areas_by_type(db: Session, area_type: str) -> List[Area]:
        """根据类型获取区域"""
        return AreaRepository.get_by_type(db, area_type)

    @staticmethod
    def update_area(db: Session, area_id: int, name: Optional[str] = None, area_type: Optional[str] = None) -> Optional[Area]:
        """更新区域"""
        area = AreaRepository.get_by_id(db, area_id)
        if not area:
            return None
        if name is not None:
            area.name = name
        if area_type is not None:
            area.type = area_type
        return AreaRepository.update(db, area)

    @staticmethod
    def delete_area(db: Session, area_id: int) -> bool:
        """删除区域"""
        area = AreaRepository.get_by_id(db, area_id)
        if not area:
            return False
        AreaRepository.delete(db, area)
        return True

    @staticmethod
    def get_exceed_ranking(
        db: Session, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 10
    ) -> List[dict]:
        """获取超标重灾区排名"""
        return AreaRepository.get_exceed_ranking(db, start_time, end_time, limit)

    @staticmethod
    def get_area_stats(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """获取各区域噪声统计"""
        return AreaRepository.get_area_stats(db, start_time, end_time)

    @staticmethod
    def count_areas(db: Session) -> int:
        """统计区域数"""
        return AreaRepository.count(db)
