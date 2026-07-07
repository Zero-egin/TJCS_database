"""
区域相关 Schema
"""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AreaBase(BaseModel):
    """区域基础字段"""
    name: str
    type: Optional[str] = None  # residential, commercial, industrial, mixed
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)


class AreaCreate(AreaBase):
    """区域创建"""
    pass


class AreaOut(AreaBase):
    """区域输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
