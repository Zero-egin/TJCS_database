"""
审计日志相关 Schema
"""
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    """审计日志输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: Optional[int]
    username: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[int]
    old_value: Optional[Dict[str, Any]]
    new_value: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    created_at: datetime


class AuditLogQuery(BaseModel):
    """审计日志查询参数"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
