"""
监测点相关 Schema
"""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MonitoringPointBase(BaseModel):
    """监测点基础字段"""
    name: str
    area_id: Optional[int] = None
    device_id: Optional[int] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    threshold_db: Decimal = Field(default=Decimal("65.00"), ge=0, le=200)


class MonitoringPointCreate(MonitoringPointBase):
    """监测点创建"""
    pass


class MonitoringPointUpdate(BaseModel):
    """监测点更新"""
    name: Optional[str] = None
    area_id: Optional[int] = None
    device_id: Optional[int] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)
    threshold_db: Optional[Decimal] = Field(None, ge=0, le=200)
    status: Optional[str] = None


class MonitoringPointOut(MonitoringPointBase):
    """监测点输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    area_name: Optional[str] = None  # 联表查询时填充
