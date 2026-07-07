"""
区域与设备管理 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import get_db, get_current_active_user, require_super_admin, require_operator_or_admin, require_permission
from app.models import User
from app.schemas import AreaCreate, AreaOut, DeviceCreate, DeviceUpdate, DeviceOut, UserOut, UserCreate, UserUpdate
from app.schemas.user import Permission
from app.services import AreaService, DeviceService, UserService

router = APIRouter(tags=["系统管理"])


# ==================== 用户管理 ====================
@router.get("/users", response_model=List[UserOut])
def list_users(
    status: Optional[str] = Query(None, description="筛选状态: active, inactive, locked, pending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """获取用户列表 (仅超级管理员)"""
    users = UserService.get_all_users(db)
    if status:
        users = [u for u in users if u.status == status]
    return [UserOut.from_user(u) for u in users]


@router.post("/users", response_model=UserOut)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """创建用户 (仅超级管理员)"""
    from app.repositories import UserRepository
    if UserRepository.get_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = UserService.create_user(db, data)
    return UserOut.from_user(user)


@router.put("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """更新用户 (仅超级管理员)"""
    from app.repositories import UserRepository
    target_user = UserRepository.get_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 不能编辑超级管理员（除非是自己编辑自己的基本信息）
    if target_user.role and target_user.role.name == "super_admin" and target_user.id != current_user.id:
        raise HTTPException(status_code=403, detail="不能编辑其他超级管理员")
    
    # 禁止通过通用更新接口把用户设为待审核状态（待审核仅用于申请流程）
    if data.status == "pending":
        raise HTTPException(status_code=400, detail="不能通过此接口将用户设为待审核状态")
    
    user = UserService.update_user(db, user_id, data)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return UserOut.from_user(user)


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """删除用户 (仅超级管理员)"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    from app.repositories import UserRepository
    target_user = UserRepository.get_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 不能删除超级管理员
    if target_user.role and target_user.role.name == "super_admin":
        raise HTTPException(status_code=403, detail="不能删除超级管理员")
    if not UserService.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}


@router.post("/users/{user_id}/approve")
def approve_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """审核通过用户申请 (仅超级管理员)"""
    user = UserService.activate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "审核通过", "user": UserOut.from_user(user)}


@router.post("/users/{user_id}/reject")
def reject_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """拒绝用户申请 (仅超级管理员)"""
    user = UserService.deactivate_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "已拒绝申请", "user": UserOut.from_user(user)}


# ==================== 区域 ====================
@router.get("/areas", response_model=List[AreaOut])
def list_areas(db: Session = Depends(get_db)):
    """获取区域列表 (所有用户可访问)"""
    areas = AreaService.get_all_areas(db)
    return [AreaOut.model_validate(a) for a in areas]


@router.post("/areas", response_model=AreaOut)
def create_area(
    data: AreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AREA_MANAGE))
):
    """创建区域 (仅超级管理员)"""
    area = AreaService.create_area(db, data)
    return AreaOut.model_validate(area)


@router.put("/areas/{area_id}", response_model=AreaOut)
def update_area(
    area_id: int,
    data: AreaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AREA_MANAGE))
):
    """更新区域 (仅超级管理员)"""
    area = AreaService.update_area(db, area_id, data)
    if not area:
        raise HTTPException(status_code=404, detail="区域不存在")
    return AreaOut.model_validate(area)


@router.delete("/areas/{area_id}")
def delete_area(
    area_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.AREA_MANAGE))
):
    """删除区域 (仅超级管理员)"""
    if not AreaService.delete_area(db, area_id):
        raise HTTPException(status_code=404, detail="区域不存在")
    return {"message": "删除成功"}


# ==================== 设备 ====================
@router.get("/devices", response_model=List[DeviceOut])
def list_devices(db: Session = Depends(get_db)):
    """获取设备列表 (所有用户可访问)"""
    devices = DeviceService.get_all_devices(db)
    return [DeviceOut.model_validate(d) for d in devices]


@router.post("/devices", response_model=DeviceOut)
def create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_or_admin)
):
    """创建设备 (运维员及以上)"""
    device = DeviceService.create_device(db, data)
    return DeviceOut.model_validate(device)


@router.put("/devices/{device_id}", response_model=DeviceOut)
def update_device(
    device_id: int,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator_or_admin)
):
    """更新设备 (运维员及以上)"""
    device = DeviceService.update_device(db, device_id, data)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return DeviceOut.model_validate(device)


@router.delete("/devices/{device_id}")
def delete_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """删除设备 (仅超级管理员)"""
    if not DeviceService.delete_device(db, device_id):
        raise HTTPException(status_code=404, detail="设备不存在")
    return {"message": "删除成功"}
