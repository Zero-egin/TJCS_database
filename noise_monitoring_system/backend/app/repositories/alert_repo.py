"""
告警数据访问层
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models import Alert, Action, MonitoringPoint, Area


class AlertRepository:
    """报警数据访问"""

    @staticmethod
    def get_by_id(db: Session, alert_id: int) -> Optional[Alert]:
        return db.query(Alert)\
            .options(joinedload(Alert.point))\
            .filter(Alert.id == alert_id)\
            .first()

    @staticmethod
    def create(db: Session, alert: Alert) -> Alert:
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_all(
        db: Session,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        area_id: Optional[int] = None,
        area_type: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        status: Optional[str] = None,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 20
    ) -> Tuple[List[Alert], int]:
        """多维联动查询"""
        query = db.query(Alert).join(MonitoringPoint).outerjoin(Area)
        
        # 默认排除已归档的告警，除非明确查询 archived 或 include_archived=True
        if status == "archived":
            query = query.filter(Alert.status == "archived")
        elif status:
            query = query.filter(Alert.status == status)
        elif not include_archived:
            query = query.filter(Alert.status != "archived")
        
        if start_time:
            query = query.filter(Alert.triggered_at >= start_time)
        if end_time:
            query = query.filter(Alert.triggered_at <= end_time)
        if area_id:
            query = query.filter(MonitoringPoint.area_id == area_id)
        if area_type:
            query = query.filter(Area.type == area_type)
        if severity:
            query = query.filter(Alert.severity == severity)
        if alert_type:
            query = query.filter(Alert.type == alert_type)

        total = query.count()
        alerts = query.options(
            joinedload(Alert.point).joinedload(MonitoringPoint.area)
        ).order_by(Alert.triggered_at.desc())\
         .offset(skip)\
         .limit(limit)\
         .all()

        return alerts, total

    @staticmethod
    def count_pending(db: Session) -> int:
        """统计待处理告警数"""
        return db.query(Alert).filter(Alert.status == "open").count()

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        """按状态统计告警数"""
        return db.query(Alert).filter(Alert.status == status).count()

    @staticmethod
    def count_exceed_points_today(db: Session) -> int:
        """获取今日有超标记录的点位数"""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        result = db.query(func.count(func.distinct(Alert.point_id))).filter(
            Alert.triggered_at >= today
        ).scalar()
        return result or 0

    @staticmethod
    def count_exceed_points_for_period(db: Session, start_time: datetime, end_time: datetime) -> int:
        """获取指定时间段有超标记录的点位数"""
        result = db.query(func.count(func.distinct(Alert.point_id))).filter(
            Alert.triggered_at >= start_time,
            Alert.triggered_at < end_time
        ).scalar()
        return result or 0

    @staticmethod
    def resolve(
        db: Session, 
        alert: Alert, 
        user_id: Optional[int], 
        notes: Optional[str],
        handler: Optional[str] = None
    ) -> Alert:
        """处理告警"""
        # 确保 alert 在当前 session 中
        if alert not in db:
            alert = db.merge(alert)
        
        alert.status = "resolved"
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = handler  # 保存处置人名称
        
        action = Action(
            alert_id=alert.id,
            action_type="resolve",
            action_by=user_id,
            notes=notes
        )
        db.add(action)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def archive(
        db: Session, 
        alert: Alert, 
        user_id: Optional[int] = None
    ) -> Alert:
        """归档告警"""
        # 确保 alert 在当前 session 中
        if alert not in db:
            alert = db.merge(alert)
        
        alert.status = "archived"
        alert.resolved_at = alert.resolved_at or datetime.utcnow()
        
        action = Action(
            alert_id=alert.id,
            action_type="archive",
            action_by=user_id,
            notes="告警已归档"
        )
        db.add(action)
        db.commit()
        db.refresh(alert)
        return alert

    @staticmethod
    def get_recent(db: Session, limit: int = 10) -> List[Alert]:
        """获取最近告警"""
        return db.query(Alert)\
            .options(joinedload(Alert.point).joinedload(MonitoringPoint.area))\
            .order_by(Alert.triggered_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def count_by_severity(db: Session, start_time: datetime, end_time: datetime) -> dict:
        """按严重程度统计告警"""
        result = db.query(
            Alert.severity,
            func.count(Alert.id)
        ).filter(
            Alert.triggered_at >= start_time,
            Alert.triggered_at <= end_time
        ).group_by(Alert.severity).all()
        
        return {row[0]: row[1] for row in result}

    @staticmethod
    def count_by_area(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """按区域统计告警"""
        result = db.query(
            Area.id,
            Area.name,
            func.count(Alert.id)
        ).join(MonitoringPoint, Alert.point_id == MonitoringPoint.id)\
         .join(Area, MonitoringPoint.area_id == Area.id)\
         .filter(
            Alert.triggered_at >= start_time,
            Alert.triggered_at <= end_time
        ).group_by(Area.id, Area.name).all()
        
        return [
            {"area_id": row[0], "area_name": row[1], "count": row[2]} 
            for row in result
        ]
