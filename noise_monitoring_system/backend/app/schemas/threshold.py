"""
阈值规则相关 Schema
"""
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ThresholdRuleBase(BaseModel):
    """阈值规则基础字段"""
    area_id: Optional[int] = None
    point_id: Optional[int] = None
    day_threshold: Decimal
    night_threshold: Decimal
    is_active: bool = True


class ThresholdRuleCreate(ThresholdRuleBase):
    """阈值规则创建"""
    pass


class ThresholdRuleUpdate(BaseModel):
    """阈值规则更新"""
    day_threshold: Optional[Decimal] = None
    night_threshold: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ThresholdRuleOut(ThresholdRuleBase):
    """阈值规则输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    area_name: Optional[str] = None
    point_name: Optional[str] = None
