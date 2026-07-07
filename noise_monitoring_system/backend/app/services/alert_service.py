"""
告警服务
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import Alert
from app.repositories import AlertRepository
from app.schemas import AlertFilterQuery


class AlertService:
    """报警服务"""

    @staticmethod
    def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """获取单条告警"""
        return AlertRepository.get_by_id(db, alert_id)

    @staticmethod
    def get_alerts(db: Session, query: AlertFilterQuery) -> Tuple[List[Alert], int]:
        """多维联动查询告警"""
        skip = (query.page - 1) * query.page_size
        
        # 解析多选状态
        statuses = query.statuses if query.statuses else None
        severities = query.severities if query.severities else None
        types = query.types if query.types else None
        
        return AlertRepository.get_all(
            db,
            start_time=query.start_time,
            end_time=query.end_time,
            area_id=query.area_id,
            severity=severities[0] if severities and len(severities) == 1 else None,
            alert_type=types[0] if types and len(types) == 1 else None,
            status=statuses[0] if statuses and len(statuses) == 1 else None,
            skip=skip,
            limit=query.page_size
        )

    @staticmethod
    def get_recent_alerts(db: Session, limit: int = 10) -> List[Alert]:
        """获取最近告警"""
        return AlertRepository.get_recent(db, limit)

    @staticmethod
    def resolve_alert(
        db: Session, 
        alert_id: int, 
        user_id: Optional[int], 
        notes: Optional[str],
        handler: Optional[str] = None
    ) -> Optional[Alert]:
        """处理告警"""
        alert = AlertRepository.get_by_id(db, alert_id)
        if not alert:
            return None
        return AlertRepository.resolve(db, alert, user_id, notes, handler)

    @staticmethod
    def count_pending(db: Session) -> int:
        """统计待处理告警数"""
        return AlertRepository.count_pending(db)

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """按状态统计告警数"""
        return AlertRepository.count_by_status(db, status)

    @staticmethod
    def archive_alert(
        db: Session, 
        alert_id: int,
        user_id: Optional[int] = None
    ) -> Optional[Alert]:
        """归档告警"""
        alert = AlertRepository.get_by_id(db, alert_id)
        if not alert:
            return None
        return AlertRepository.archive(db, alert, user_id)

    @staticmethod
    def count_exceed_points_today(db: Session) -> int:
        """获取今日超标点位数"""
        return AlertRepository.count_exceed_points_today(db)

    @staticmethod
    def get_severity_distribution(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> dict:
        """获取告警严重程度分布"""
        return AlertRepository.count_by_severity(db, start_time, end_time)

    @staticmethod
    def get_area_distribution(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """获取告警区域分布"""
        return AlertRepository.count_by_area(db, start_time, end_time)
