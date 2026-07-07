"""
统计相关 Schema
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TimeRangeQuery(BaseModel):
    """时间范围查询参数"""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    area_id: Optional[int] = None
    point_id: Optional[int] = None


class DailyStatsOut(BaseModel):
    """每日统计"""
    model_config = ConfigDict(from_attributes=True)
    date: date
    area_id: Optional[int] = None
    area_name: Optional[str] = None
    avg_db: Decimal
    max_db: Decimal
    min_db: Decimal
    exceed_count: int
    sample_count: int


class HourlyTrendOut(BaseModel):
    """小时趋势"""
    model_config = ConfigDict(from_attributes=True)
    hour: int
    avg_db: Decimal
    max_db: Decimal
    min_db: Decimal


class AreaRankingOut(BaseModel):
    """区域排名"""
    model_config = ConfigDict(from_attributes=True)
    area_id: int
    area_name: str
    avg_db: Decimal
    exceed_rate: Decimal
    alert_count: int
    rank: int


class OverviewStatsOut(BaseModel):
    """概览统计"""
    total_points: int
    total_areas: int
    today_readings: int
    today_avg_db: Optional[Decimal] = None
    active_alerts: int
    exceed_rate: Optional[Decimal] = None
    data_date: Optional[str] = None  # 数据参考日期


class PointTrendOut(BaseModel):
    """监测点趋势"""
    model_config = ConfigDict(from_attributes=True)
    time_bucket: datetime
    point_id: int
    point_name: Optional[str] = None
    avg_db: Decimal
    max_db: Decimal
    min_db: Decimal


class AggregatedStatsOut(BaseModel):
    """聚合统计结果"""
    model_config = ConfigDict(from_attributes=True)
    time_bucket: datetime
    avg_db: Decimal
    max_db: Decimal
    min_db: Decimal
    sample_count: int
