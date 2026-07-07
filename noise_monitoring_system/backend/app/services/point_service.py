"""
监测点管理服务
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import MonitoringPoint
from app.repositories import MonitoringPointRepository
from app.schemas import MonitoringPointCreate, MonitoringPointUpdate


class MonitoringPointService:
    """监测点管理服务"""

    @staticmethod
    def create_point(db: Session, data: MonitoringPointCreate) -> MonitoringPoint:
        """创建监测点"""
        point = MonitoringPoint(
            name=data.name,
            area_id=data.area_id,
            device_id=data.device_id,
            latitude=data.latitude,
            longitude=data.longitude,
            threshold_db=data.threshold_db
        )
        return MonitoringPointRepository.create(db, point)

    @staticmethod
    def get_point(db: Session, point_id: int) -> Optional[MonitoringPoint]:
        """获取监测点"""
        return MonitoringPointRepository.get_by_id(db, point_id)

    @staticmethod
    def get_all_points(
        db: Session, 
        area_id: Optional[int] = None, 
        status: Optional[str] = None
    ) -> List[MonitoringPoint]:
        """获取所有监测点"""
        return MonitoringPointRepository.get_all(db, area_id, status)

    @staticmethod
    def get_points_for_map(db: Session, reference_time: Optional[datetime] = None) -> List[dict]:
        """获取地图展示所需的点位数据（含噪声值）
        
        Args:
            db: 数据库会话
            reference_time: 历史数据参考时间，如果不传则返回最新数据
        """
        return MonitoringPointRepository.get_points_with_reading_at_time(db, reference_time)

    @staticmethod
    def get_points_by_area_type(db: Session, area_type: str) -> List[MonitoringPoint]:
        """根据区域类型获取监测点"""
        return MonitoringPointRepository.get_points_by_area_type(db, area_type)

    @staticmethod
    def search_points(db: Session, name: str) -> List[MonitoringPoint]:
        """搜索监测点"""
        return MonitoringPointRepository.search_by_name(db, name)

    @staticmethod
    def update_point(
        db: Session, 
        point_id: int, 
        data: MonitoringPointUpdate
    ) -> Optional[MonitoringPoint]:
        """更新监测点"""
        point = MonitoringPointRepository.get_by_id(db, point_id)
        if not point:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(point, field, value)
        return MonitoringPointRepository.update(db, point)

    @staticmethod
    def delete_point(db: Session, point_id: int) -> bool:
        """删除监测点"""
        point = MonitoringPointRepository.get_by_id(db, point_id)
        if not point:
            return False
        MonitoringPointRepository.delete(db, point)
        return True

    @staticmethod
    def activate_point(db: Session, point_id: int) -> Optional[MonitoringPoint]:
        """激活监测点"""
        point = MonitoringPointRepository.get_by_id(db, point_id)
        if not point:
            return None
        point.status = "active"
        return MonitoringPointRepository.update(db, point)

    @staticmethod
    def deactivate_point(db: Session, point_id: int) -> Optional[MonitoringPoint]:
        """停用监测点"""
        point = MonitoringPointRepository.get_by_id(db, point_id)
        if not point:
            return None
        point.status = "inactive"
        return MonitoringPointRepository.update(db, point)

    @staticmethod
    def count_points(db: Session) -> int:
        """统计监测点总数"""
        return MonitoringPointRepository.count(db)

    @staticmethod
    def count_active_points(db: Session) -> int:
        """统计活跃监测点数"""
        return MonitoringPointRepository.count_active(db)
