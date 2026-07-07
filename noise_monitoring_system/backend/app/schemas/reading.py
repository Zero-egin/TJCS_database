"""
噪声数据相关 Schema
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NoiseReadingBase(BaseModel):
    """噪声数据基础字段"""
    point_id: int
    measured_at: datetime
    db_value: Decimal = Field(ge=0, le=200)
    temperature: Optional[Decimal] = None
    humidity: Optional[Decimal] = None


class NoiseReadingCreate(NoiseReadingBase):
    """噪声数据创建"""
    device_id: Optional[int] = None


class NoiseReadingBulkCreate(BaseModel):
    """批量导入"""
    readings: List[NoiseReadingCreate]


class NoiseReadingOut(NoiseReadingBase):
    """噪声数据输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_exceed: bool
    point_name: Optional[str] = None


class IngestionJobOut(BaseModel):
    """数据导入任务输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    source: Optional[str]
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    records_count: int
