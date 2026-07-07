"""
审计日志数据访问层
"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models import AuditLog, User


class AuditLogRepository:
    """审计日志数据访问"""

    @staticmethod
    def create(db: Session, log: AuditLog) -> AuditLog:
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def get_by_id(db: Session, log_id: int) -> Optional[AuditLog]:
        return db.get(AuditLog, log_id)

    @staticmethod
    def get_all(
        db: Session,
        user_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[AuditLog], int]:
        """多条件查询审计日志"""
        query = db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_time:
            query = query.filter(AuditLog.created_at >= start_time)
        if end_time:
            query = query.filter(AuditLog.created_at <= end_time)

        total = query.count()
        logs = query.order_by(AuditLog.created_at.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        return logs, total

    @staticmethod
    def get_recent(db: Session, limit: int = 20) -> List[AuditLog]:
        """获取最近的审计日志"""
        return db.query(AuditLog)\
            .order_by(AuditLog.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_by_user(db: Session, user_id: int, limit: int = 50) -> List[AuditLog]:
        """获取指定用户的操作日志"""
        return db.query(AuditLog)\
            .filter(AuditLog.user_id == user_id)\
            .order_by(AuditLog.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def get_by_resource(
        db: Session, 
        resource_type: str, 
        resource_id: int
    ) -> List[AuditLog]:
        """获取指定资源的操作日志"""
        return db.query(AuditLog)\
            .filter(
                AuditLog.resource_type == resource_type,
                AuditLog.resource_id == resource_id
            )\
            .order_by(AuditLog.created_at.desc())\
            .all()
