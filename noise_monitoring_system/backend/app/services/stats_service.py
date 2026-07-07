"""
统计分析服务
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.repositories import (
    NoiseReadingRepository, 
    AlertRepository, 
    AreaRepository,
    MonitoringPointRepository
)
from app.schemas import OverviewStatsOut
from app.services.device_service import DeviceService


class StatsService:
    """统计分析服务"""

    @staticmethod
    def get_data_time_range(db: Session) -> dict:
        """获取数据库中噪声数据的时间范围"""
        return NoiseReadingRepository.get_time_range(db)

    @staticmethod
    def get_overview(
        db: Session, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> OverviewStatsOut:
        """获取仪表盘概览数据
        
        Args:
            db: 数据库会话
            start_time: 开始时间
            end_time: 结束时间
        """
        # 获取数据时间范围
        time_range = NoiseReadingRepository.get_time_range(db)
        
        # 如果没有指定时间范围，使用数据集最新日期的全天
        if start_time is None or end_time is None:
            if time_range and time_range.get('max_time'):
                reference_date = time_range['max_time']
            else:
                reference_date = datetime.utcnow()
            day_start = reference_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
        else:
            day_start = start_time
            day_end = end_time
            reference_date = start_time
        
        # 获取统计数据
        avg_db = NoiseReadingRepository.get_avg_for_period(db, day_start, day_end)
        day_readings = NoiseReadingRepository.get_count_for_period(db, day_start, day_end)
        exceed_points = AlertRepository.count_exceed_points_for_period(db, day_start, day_end)
        pending_alerts = AlertRepository.count_pending(db)
        total_points = MonitoringPointRepository.count(db)
        total_areas = AreaRepository.count(db)

        # 计算当日超标率
        exceed_rate = NoiseReadingRepository.get_exceed_rate(
            db, day_start, day_end
        ) if day_readings > 0 else Decimal("0")

        return OverviewStatsOut(
            total_points=total_points,
            total_areas=total_areas,
            today_readings=day_readings,
            today_avg_db=avg_db if avg_db else None,
            active_alerts=pending_alerts,
            exceed_rate=exceed_rate if exceed_rate else None,
            data_date=reference_date.strftime('%Y-%m-%d') if reference_date else None
        )

    @staticmethod
    def get_area_ranking(
        db: Session, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 10
    ) -> List[dict]:
        """获取超标重灾区排名"""
        return AreaRepository.get_exceed_ranking(db, start_time, end_time, limit)

    @staticmethod
    def get_area_stats(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """获取各区域噪声统计"""
        return AreaRepository.get_area_stats(db, start_time, end_time)

    @staticmethod
    def get_hourly_trend(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        point_id: Optional[int] = None
    ) -> List[dict]:
        """获取小时趋势数据"""
        return NoiseReadingRepository.get_hourly_trend(
            db, start_time, end_time, point_id
        )

    @staticmethod
    def get_daily_stats(
        db: Session,
        start_time: datetime,
        end_time: datetime,
        area_id: Optional[int] = None
    ) -> List[dict]:
        """获取每日统计数据"""
        return NoiseReadingRepository.get_daily_stats(
            db, start_time, end_time, area_id
        )

    @staticmethod
    def get_alert_severity_distribution(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> dict:
        """获取告警严重程度分布"""
        return AlertRepository.count_by_severity(db, start_time, end_time)

    @staticmethod
    def get_alert_area_distribution(
        db: Session, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[dict]:
        """获取告警区域分布"""
        return AlertRepository.count_by_area(db, start_time, end_time)

    @staticmethod
    def get_time_bucket_data(
        db: Session, 
        start_time: datetime, 
        end_time: datetime, 
        interval: str = "1 hour"
    ) -> List[dict]:
        """获取时间桶聚合数据（用于时间轴回溯）"""
        return NoiseReadingRepository.get_time_bucket_data(
            db, start_time, end_time, interval
        )
