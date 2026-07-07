"""
Service Package - 业务逻辑层

遵循高内聚、低耦合原则，按领域拆分为独立模块：
- auth_service: 认证服务
- user_service: 用户管理服务
- area_service: 区域管理服务
- device_service: 设备管理服务
- point_service: 监测点管理服务
- data_service: 噪声数据服务 (含导入引擎)
- alert_service: 告警服务
- stats_service: 统计分析服务
- audit_service: 审计日志服务
"""

# 认证
from .auth_service import AuthService

# 用户管理
from .user_service import UserService

# 区域管理
from .area_service import AreaService

# 设备管理
from .device_service import DeviceService

# 监测点管理
from .point_service import MonitoringPointService

# 噪声数据
from .data_service import NoiseDataService

# 告警
from .alert_service import AlertService

# 统计分析
from .stats_service import StatsService

# 审计日志
from .audit_service import AuditService

__all__ = [
    "AuthService",
    "UserService",
    "AreaService",
    "DeviceService",
    "MonitoringPointService",
    "NoiseDataService",
    "AlertService",
    "StatsService",
    "AuditService",
]
