"""
Schemas Package - 数据传输对象 (DTOs / Pydantic Models)

遵循高内聚、低耦合原则，按领域拆分为独立模块：
- common: 通用响应格式
- user: 用户认证相关
- area: 区域相关
- device: 设备相关
- point: 监测点相关
- reading: 噪声数据相关
- alert: 告警相关
- stats: 统计相关
- threshold: 阈值规则相关
- audit: 审计日志相关
"""

# 通用
from .common import PaginatedResponse, ResponseBase

# 用户认证
from .user import (
    TokenOut, 
    UserBase, 
    UserCreate, 
    UserLogin, 
    UserOut, 
    UserUpdate,
    RoleEnum,
    RoleOut,
    Permission,
    ROLE_PERMISSIONS,
    PasswordChange,
    PasswordReset,
    get_user_permissions,
)

# 区域
from .area import AreaBase, AreaCreate, AreaOut

# 设备
from .device import DeviceBase, DeviceCreate, DeviceUpdate, DeviceOut

# 监测点
from .point import (
    MonitoringPointBase,
    MonitoringPointCreate,
    MonitoringPointOut,
    MonitoringPointUpdate,
)

# 噪声数据
from .reading import (
    IngestionJobOut,
    NoiseReadingBase,
    NoiseReadingBulkCreate,
    NoiseReadingCreate,
    NoiseReadingOut,
)

# 告警
from .alert import AlertBase, AlertFilterQuery, AlertOut, AlertResolve

# 统计
from .stats import (
    AggregatedStatsOut,
    AreaRankingOut,
    DailyStatsOut,
    HourlyTrendOut,
    OverviewStatsOut,
    PointTrendOut,
    TimeRangeQuery,
)

# 阈值规则
from .threshold import (
    ThresholdRuleBase,
    ThresholdRuleCreate,
    ThresholdRuleOut,
    ThresholdRuleUpdate,
)

# 审计日志
from .audit import AuditLogOut, AuditLogQuery

__all__ = [
    # common
    "ResponseBase",
    "PaginatedResponse",
    # user
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserOut",
    "UserLogin",
    "TokenOut",
    # area
    "AreaBase",
    "AreaCreate",
    "AreaOut",
    # device
    "DeviceBase",
    "DeviceCreate",
    "DeviceUpdate",
    "DeviceOut",
    # point
    "MonitoringPointBase",
    "MonitoringPointCreate",
    "MonitoringPointUpdate",
    "MonitoringPointOut",
    # reading
    "NoiseReadingBase",
    "NoiseReadingCreate",
    "NoiseReadingBulkCreate",
    "NoiseReadingOut",
    "IngestionJobOut",
    # alert
    "AlertBase",
    "AlertOut",
    "AlertResolve",
    "AlertFilterQuery",
    # stats
    "TimeRangeQuery",
    "DailyStatsOut",
    "HourlyTrendOut",
    "AreaRankingOut",
    "OverviewStatsOut",
    "PointTrendOut",
    "AggregatedStatsOut",
    # threshold
    "ThresholdRuleBase",
    "ThresholdRuleCreate",
    "ThresholdRuleUpdate",
    "ThresholdRuleOut",
    # audit
    "AuditLogOut",
    "AuditLogQuery",
]
