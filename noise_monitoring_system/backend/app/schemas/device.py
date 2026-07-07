"""
设备相关 Schema
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DeviceBase(BaseModel):
    """设备基础字段"""
    serial_no: str
    model: Optional[str] = None


class DeviceCreate(DeviceBase):
    """设备创建"""
    status: Optional[str] = "active"


class DeviceUpdate(BaseModel):
    """设备更新"""
    serial_no: Optional[str] = None
    model: Optional[str] = None
    status: Optional[str] = None


class DeviceOut(DeviceBase):
    """设备输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    installed_at: Optional[datetime] = None
