"""
Repository Package - 数据访问层 (DAO Layer)

遵循高内聚、低耦合原则，按领域拆分为独立模块：
- base: 通用基类和工具
- user_repo: 用户数据访问
- area_repo: 区域数据访问
- device_repo: 设备数据访问
- point_repo: 监测点数据访问
- reading_repo: 噪声数据访问 (TimescaleDB)
- alert_repo: 告警数据访问
- job_repo: 数据导入任务数据访问
- threshold_repo: 阈值规则数据访问
- audit_repo: 审计日志数据访问
"""

# 基类
from .base import BaseRepository

# 用户
from .user_repo import UserRepository

# 区域
from .area_repo import AreaRepository

# 设备
from .device_repo import DeviceRepository

# 监测点
from .point_repo import MonitoringPointRepository

# 噪声数据
from .reading_repo import NoiseReadingRepository

# 告警
from .alert_repo import AlertRepository

# 数据导入任务
from .job_repo import IngestionJobRepository

# 阈值规则
from .threshold_repo import ThresholdRuleRepository

# 审计日志
from .audit_repo import AuditLogRepository

__all__ = [
    "BaseRepository",
    "UserRepository",
    "AreaRepository",
    "DeviceRepository",
    "MonitoringPointRepository",
    "NoiseReadingRepository",
    "AlertRepository",
    "IngestionJobRepository",
    "ThresholdRuleRepository",
    "AuditLogRepository",
]
