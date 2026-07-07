"""
认证 API 路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core import get_db, create_access_token, get_current_active_user, require_super_admin
from app.core.security import verify_password, hash_password
from app.models import User
from app.schemas import UserLogin, TokenOut, UserOut, UserCreate
from app.schemas.user import PasswordChange, PasswordReset, get_user_permissions, RoleOut
from app.services import AuthService, UserService
from app.repositories import UserRepository

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = AuthService.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 根据不同状态返回不同的错误信息
    if user.status == "inactive":
        raise HTTPException(status_code=400, detail="账号已被停用，请联系管理员")
    elif user.status == "locked":
        raise HTTPException(status_code=400, detail="账号已被锁定，请联系管理员")
    elif user.status == "pending":
        raise HTTPException(status_code=400, detail="账号正在审核中，请等待管理员审核")
    elif user.status != "active":
        raise HTTPException(status_code=400, detail="账号状态异常，请联系管理员")
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # 获取用户权限列表
    permissions = []
    if user.role:
        permissions = get_user_permissions(user.role.name)
    
    return TokenOut(
        access_token=access_token,
        user=UserOut.from_user(user),
        permissions=permissions
    )


@router.post("/register", response_model=UserOut)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    if UserRepository.get_by_username(db, data.username):
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    from app.models import Role
    
    # 注册一律为普通用户；区域运维员只能由管理员后续赋权
    data.role = None
    public_role = db.query(Role).filter(Role.name == "public_user").first()
    if public_role:
        data.role_id = public_role.id
    data.status = "active"
    
    user = UserService.create_user(db, data)
    return UserOut.from_user(user)



@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_active_user)):
    """获取当前用户信息"""
    return UserOut.from_user(current_user)


@router.get("/me/permissions", response_model=List[str])
def get_my_permissions(current_user: User = Depends(get_current_active_user)):
    """获取当前用户的权限列表"""
    if not current_user.role:
        return []
    return get_user_permissions(current_user.role.name)


@router.post("/change-password")
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """修改个人密码（所有用户）"""
    # 验证旧密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    # 更新密码
    current_user.password_hash = hash_password(data.new_password)
    UserRepository.update(db, current_user)
    
    return {"message": "密码修改成功"}


@router.post("/reset-password")
def reset_password(
    data: PasswordReset,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """重置他人密码（仅超级管理员）"""
    user = UserRepository.get_by_id(db, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 不能重置自己的密码（应该用 change-password）
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能使用此接口重置自己的密码")
    
    user.password_hash = hash_password(data.new_password)
    UserRepository.update(db, user)
    
    return {"message": f"用户 {user.username} 的密码已重置"}


@router.get("/roles", response_model=List[RoleOut])
def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    """获取所有角色列表（仅超级管理员）"""
    from app.models import Role
    roles = db.query(Role).all()
    return [RoleOut.model_validate(r) for r in roles]
