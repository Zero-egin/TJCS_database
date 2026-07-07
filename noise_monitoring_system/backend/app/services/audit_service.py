"""
审计日志服务
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models import AuditLog
from app.repositories import AuditLogRepository
from app.schemas import AuditLogQuery


class AuditService:
    """审计日志服务"""

    @staticmethod
    def log(
        db: Session, 
        user_id: Optional[int], 
        action: str, 
        resource_type: str,
        resource_id: Optional[int] = None,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            user_id=user_id, 
            action=action, 
            resource_type=resource_type,
            resource_id=resource_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address
        )
        return AuditLogRepository.create(db, log)

    @staticmethod
    def log_create(
        db: Session,
        user_id: Optional[int],
        resource_type: str,
        resource_id: int,
        new_value: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录创建操作"""
        return AuditService.log(
            db, user_id, "create", resource_type, resource_id,
            None, new_value, ip_address
        )

    @staticmethod
    def log_update(
        db: Session,
        user_id: Optional[int],
        resource_type: str,
        resource_id: int,
        old_value: Dict[str, Any],
        new_value: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录更新操作"""
        return AuditService.log(
            db, user_id, "update", resource_type, resource_id,
            old_value, new_value, ip_address
        )

    @staticmethod
    def log_delete(
        db: Session,
        user_id: Optional[int],
        resource_type: str,
        resource_id: int,
        old_value: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录删除操作"""
        return AuditService.log(
            db, user_id, "delete", resource_type, resource_id,
            old_value, None, ip_address
        )

    @staticmethod
    def log_login(
        db: Session,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录登录操作"""
        return AuditService.log(
            db, user_id, "login", "user", user_id,
            None, None, ip_address
        )

    @staticmethod
    def log_logout(
        db: Session,
        user_id: int,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """记录登出操作"""
        return AuditService.log(
            db, user_id, "logout", "user", user_id,
            None, None, ip_address
        )

    @staticmethod
    def get_logs(db: Session, query: AuditLogQuery) -> Tuple[List[AuditLog], int]:
        """查询审计日志"""
        skip = (query.page - 1) * query.page_size
        return AuditLogRepository.get_all(
            db,
            user_id=query.user_id,
            action=query.action,
            resource_type=query.resource_type,
            start_time=query.start_time,
            end_time=query.end_time,
            skip=skip,
            limit=query.page_size
        )

    @staticmethod
    def get_recent_logs(db: Session, limit: int = 20) -> List[AuditLog]:
        """获取最近的审计日志"""
        return AuditLogRepository.get_recent(db, limit)

    @staticmethod
    def get_user_logs(db: Session, user_id: int, limit: int = 50) -> List[AuditLog]:
        """获取用户操作日志"""
        return AuditLogRepository.get_by_user(db, user_id, limit)

    @staticmethod
    def get_resource_logs(
        db: Session, 
        resource_type: str, 
        resource_id: int
    ) -> List[AuditLog]:
        """获取资源操作日志"""
        return AuditLogRepository.get_by_resource(db, resource_type, resource_id)
