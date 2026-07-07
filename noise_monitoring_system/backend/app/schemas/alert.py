"""
告警相关 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    """告警基础字段"""
    reading_id: int
    point_id: int
    type: str  # threshold/anomaly/trend
    severity: str  # low/medium/high/critical
    description: Optional[str] = None


class AlertOut(BaseModel):
    """告警输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    reading_id: Optional[int] = None
    point_id: int
    point_name: Optional[str] = None
    area_name: Optional[str] = None
    area_type: Optional[str] = None
    db_value: Optional[Decimal] = None
    threshold_db: Optional[Decimal] = None
    type: str
    severity: str
    status: str
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by_name: Optional[str] = None  # 处置人名称
    handler: Optional[str] = None  # 处置人名称(别名)
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AlertResolve(BaseModel):
    """告警处理"""
    notes: Optional[str] = None  # 处置措施/备注
    handler: Optional[str] = None  # 处置人名称


class AlertFilterQuery(BaseModel):
    """告警筛选参数"""
    statuses: Optional[List[str]] = None
    severities: Optional[List[str]] = None
    types: Optional[List[str]] = None
    area_id: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
