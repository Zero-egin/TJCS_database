"""
FastAPI 依赖注入
"""
from typing import List, Callable
from functools import wraps
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.core.security import decode_token
from app.schemas.user import RoleEnum, Permission, ROLE_PERMISSIONS, get_user_permissions


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_db():
    """数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """从 JWT Token 中解析当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = decode_token(token)
    if payload is None:
        print(f"[Auth] Token 解码失败: {token[:20]}...")
        raise credentials_exception
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        print(f"[Auth] Token 中没有 sub 字段: {payload}")
        raise credentials_exception
    
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        print(f"[Auth] Token 中 sub 字段不是有效的用户ID: {user_id_str}")
        raise credentials_exception

    from app.repositories.user_repo import UserRepository
    user = UserRepository.get_by_id(db, user_id)
    if user is None:
        print(f"[Auth] 用户不存在: user_id={user_id}")
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """确保用户状态为活跃"""
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def has_permission(user: User, permission: str) -> bool:
    """检查用户是否具有指定权限"""
    if not user.role:
        return False
    return permission in get_user_permissions(user.role.name)


def has_any_permission(user: User, permissions: List[str]) -> bool:
    """检查用户是否具有任一指定权限"""
    if not user.role:
        return False
    user_permissions = get_user_permissions(user.role.name)
    return any(p in user_permissions for p in permissions)


def require_permission(permission: str):
    """权限检查依赖注入工厂
    
    用法:
        @router.post("/users")
        def create_user(
            ...,
            current_user: User = Depends(require_permission(Permission.USER_MANAGE))
        ):
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要权限: {permission}"
            )
        return current_user
    return permission_checker


def require_any_permission(permissions: List[str]):
    """任一权限检查依赖注入工厂
    
    用法:
        @router.post("/points")
        def create_point(
            ...,
            current_user: User = Depends(require_any_permission([Permission.POINT_MANAGE, Permission.AREA_MANAGE]))
        ):
    """
    def permission_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not has_any_permission(current_user, permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要以下任一权限: {', '.join(permissions)}"
            )
        return current_user
    return permission_checker


def require_role(role_name: str):
    """角色检查依赖注入工厂
    
    用法:
        @router.delete("/users/{user_id}")
        def delete_user(
            ...,
            current_user: User = Depends(require_role("super_admin"))
        ):
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role or current_user.role.name != role_name:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要{role_name}角色权限"
            )
        return current_user
    return role_checker


def require_roles(role_names: List[str]):
    """多角色检查依赖注入工厂（满足任一角色即可）
    
    用法:
        @router.post("/points")
        def create_point(
            ...,
            current_user: User = Depends(require_roles(["super_admin", "area_operator"]))
        ):
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.role or current_user.role.name not in role_names:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(role_names)}"
            )
        return current_user
    return role_checker


# ==================== 快捷权限依赖 ====================

def require_super_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求超级管理员权限"""
    if not current_user.role or current_user.role.name != RoleEnum.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="需要超级管理员权限")
    return current_user


def require_operator_or_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求区域运维员或超级管理员权限"""
    if not current_user.role or current_user.role.name not in [
        RoleEnum.SUPER_ADMIN.value, 
        RoleEnum.AREA_OPERATOR.value
    ]:
        raise HTTPException(status_code=403, detail="需要运维员或管理员权限")
    return current_user


# 保持向后兼容
def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """要求管理员权限（兼容旧代码）"""
    if not current_user.role or current_user.role.name != RoleEnum.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
