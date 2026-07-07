"""
统计分析 API 路由
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core import get_db
from app.schemas import OverviewStatsOut
from app.services import StatsService, NoiseDataService

router = APIRouter(prefix="/stats", tags=["统计分析"])


@router.get("/data-range")
def get_data_time_range(db: Session = Depends(get_db)):
    """获取数据库中噪声数据的时间范围"""
    return StatsService.get_data_time_range(db)


@router.get("/overview", response_model=OverviewStatsOut)
def get_overview(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """获取仪表盘概览数据"""
    return StatsService.get_overview(db, start_time, end_time)


@router.get("/area-ranking")
def get_area_ranking(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """获取超标重灾区排名"""
    # 如果没有指定时间范围，使用数据集的最近30天
    if not start_time or not end_time:
        time_range = StatsService.get_data_time_range(db)
        if time_range and time_range.get('max_time'):
            end_time = time_range['max_time']
            start_time = end_time - timedelta(days=30)
        else:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
    
    return StatsService.get_area_ranking(db, start_time, end_time)


@router.get("/area-stats")
def get_area_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db)
):
    """获取各区域噪声统计（含平均分贝）"""
    # 如果没有指定时间范围，使用数据集的最近30天
    if not start_time or not end_time:
        time_range = StatsService.get_data_time_range(db)
        if time_range and time_range.get('max_time'):
            end_time = time_range['max_time']
            start_time = end_time - timedelta(days=30)
        else:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
    
    return StatsService.get_area_stats(db, start_time, end_time)


@router.get("/hourly-trend")
def get_hourly_trend(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    point_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取小时级别噪声趋势"""
    # 如果没有指定时间范围，使用数据集最新一天的数据
    if not start_time or not end_time:
        time_range = StatsService.get_data_time_range(db)
        if time_range and time_range.get('max_time'):
            end_time = time_range['max_time']
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end_time = datetime.utcnow()
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    return NoiseDataService.get_hourly_trend(db, start_time, end_time, point_id)


@router.get("/daily-stats")
def get_daily_stats(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    area_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """获取每日统计数据（用于月度分析）"""
    # 如果没有指定时间范围，使用数据集最近一个月的数据
    if not start_time or not end_time:
        time_range = StatsService.get_data_time_range(db)
        if time_range and time_range.get('max_time'):
            end_time = time_range['max_time']
            # 默认显示最近30天
            start_time = end_time - timedelta(days=30)
        else:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
    
    return StatsService.get_daily_stats(db, start_time, end_time, area_id)
