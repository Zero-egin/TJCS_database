"""
用户相关 Schema
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
import re

from pydantic import BaseModel, ConfigDict, field_validator


class RoleEnum(str, Enum):
    """角色枚举
    三级权限体系:
    - super_admin: 超级管理员 - 系统运维与全局监管者
    - area_operator: 区域运维员 - 一线环境治理执行者
    - public_user: 普通用户/市民 - 数据知情者与使用者
    """
    SUPER_ADMIN = "super_admin"
    AREA_OPERATOR = "area_operator"
    PUBLIC_USER = "public_user"


class RoleOut(BaseModel):
    """角色输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None


class UserBase(BaseModel):
    """用户基础字段"""
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role_id: Optional[int] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None or v == '':
            return None
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None or v == '':
            return None
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, v):
            raise ValueError('手机号格式不正确，需要11位有效手机号')
        return v


class UserCreate(UserBase):
    """用户创建"""
    password: str
    role: Optional[str] = None  # 接收前端传来的角色名称 (public_user, area_operator)
    status: Optional[str] = "active"


class UserUpdate(BaseModel):
    """用户更新"""
    email: Optional[str] = None
    phone: Optional[str] = None
    real_name: Optional[str] = None
    role_id: Optional[int] = None
    status: Optional[str] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is None or v == '':
            return None
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('邮箱格式不正确')
        return v
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v is None or v == '':
            return None
        phone_pattern = r'^1[3-9]\d{9}$'
        if not re.match(phone_pattern, v):
            raise ValueError('手机号格式不正确，需要11位有效手机号')
        return v


class PasswordChange(BaseModel):
    """修改密码"""
    old_password: str
    new_password: str


class PasswordReset(BaseModel):
    """重置他人密码(管理员使用)"""
    user_id: int
    new_password: str


class UserOut(UserBase):
    """用户输出"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
    role_name: Optional[str] = None
    
    @classmethod
    def from_user(cls, user):
        """从User模型创建UserOut，包含角色名"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            real_name=user.real_name,
            role_id=user.role_id,
            status=user.status,
            created_at=user.created_at,
            role_name=user.role.name if user.role else None
        )


class UserLogin(BaseModel):
    """用户登录"""
    username: str
    password: str


class TokenOut(BaseModel):
    """Token 输出"""
    access_token: str
    token_type: str = "bearer"
    user: UserOut
    permissions: List[str] = []  # 用户拥有的权限列表


# ==================== 权限定义 ====================
class Permission:
    """权限常量定义
    
    功能模块与权限项对照:
    - 用户管理: user_manage(增删用户/重置他人密码), password_change(修改个人密码)
    - 区域管理: area_manage(设置区域范围与噪声阈值)
    - 监测点管理: point_manage(部署/删除点位), point_view(查看点位详情)
    - 数据导入: data_import(执行ETL), data_clean(清理/修正历史数据)
    - 报警管理: alert_resolve(标记处理状态), alert_manage(删除/归档)
    - 统计分析: stats_view(查看看板与报表)
    """
    # 用户管理
    USER_MANAGE = "user_manage"           # 增删用户 / 重置他人密码
    PASSWORD_CHANGE = "password_change"   # 修改个人密码
    
    # 区域管理
    AREA_MANAGE = "area_manage"           # 设置区域范围与噪声阈值
    
    # 监测点管理
    POINT_MANAGE = "point_manage"         # 部署/删除点位坐标
    POINT_VIEW = "point_view"             # 查看点位详情
    
    # 数据导入
    DATA_IMPORT = "data_import"           # 执行大规模数据集导入 (ETL)
    DATA_CLEAN = "data_clean"             # 清理/修正历史错误数据
    
    # 报警管理
    ALERT_RESOLVE = "alert_resolve"       # 标记报警处理状态 (Resolve)
    ALERT_MANAGE = "alert_manage"         # 删除/归档报警记录
    
    # 统计分析
    STATS_VIEW = "stats_view"             # 查看全市治理看板与报表


# 角色权限映射表
ROLE_PERMISSIONS = {
    RoleEnum.SUPER_ADMIN: [
        Permission.USER_MANAGE,
        Permission.PASSWORD_CHANGE,
        Permission.AREA_MANAGE,
        Permission.POINT_MANAGE,
        Permission.POINT_VIEW,
        Permission.DATA_IMPORT,
        Permission.DATA_CLEAN,
        Permission.ALERT_MANAGE,
        Permission.STATS_VIEW,
    ],
    RoleEnum.AREA_OPERATOR: [
        Permission.PASSWORD_CHANGE,
        Permission.POINT_MANAGE,
        Permission.POINT_VIEW,
        Permission.DATA_IMPORT,
        Permission.ALERT_RESOLVE,
        Permission.STATS_VIEW,
    ],
    RoleEnum.PUBLIC_USER: [
        Permission.PASSWORD_CHANGE,
        Permission.POINT_VIEW,
        Permission.STATS_VIEW,
    ],
}


def get_user_permissions(role_name: str) -> List[str]:
    """根据角色名获取权限列表"""
    try:
        role_enum = RoleEnum(role_name)
        return ROLE_PERMISSIONS.get(role_enum, [])
    except ValueError:
        return []
