"""
用户管理服务
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User, Role
from app.repositories import UserRepository
from app.schemas import UserCreate, UserUpdate
from app.schemas.user import RoleEnum


class UserService:
    """用户管理服务"""

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        """创建用户"""
        # 如果未指定角色，默认为普通用户
        role_id = data.role_id
        if role_id is None:
            public_role = db.query(Role).filter(Role.name == RoleEnum.PUBLIC_USER.value).first()
            if public_role:
                role_id = public_role.id
        
        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
            email=data.email,
            phone=data.phone,
            real_name=data.real_name,
            role_id=role_id,
            status=data.status if data.status else "active"
        )
        return UserRepository.create(db, user)

    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """获取用户"""
        return UserRepository.get_by_id(db, user_id)

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        return UserRepository.get_by_username(db, username)

    @staticmethod
    def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """获取所有用户"""
        return UserRepository.get_all(db, skip, limit)
    
    @staticmethod
    def get_users_by_role(db: Session, role_name: str, skip: int = 0, limit: int = 100) -> List[User]:
        """根据角色获取用户列表"""
        return db.query(User).join(Role).filter(Role.name == role_name).offset(skip).limit(limit).all()

    @staticmethod
    def update_user(db: Session, user_id: int, data: UserUpdate) -> Optional[User]:
        """更新用户"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        if data.email is not None:
            user.email = data.email
        if data.phone is not None:
            user.phone = data.phone
        if data.real_name is not None:
            user.real_name = data.real_name
        if data.role_id is not None:
            user.role_id = data.role_id
        if data.status is not None:
            user.status = data.status
        return UserRepository.update(db, user)

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """删除用户"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return False
        UserRepository.delete(db, user)
        return True

    @staticmethod
    def activate_user(db: Session, user_id: int) -> Optional[User]:
        """激活用户"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        user.status = "active"
        return UserRepository.update(db, user)

    @staticmethod
    def deactivate_user(db: Session, user_id: int) -> Optional[User]:
        """停用用户"""
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        user.status = "inactive"
        return UserRepository.update(db, user)

    @staticmethod
    def count_users(db: Session) -> int:
        """统计用户数"""
        return UserRepository.count(db)

    @staticmethod
    def count_active_users(db: Session) -> int:
        """统计活跃用户数"""
        return UserRepository.count_active(db)
    
    @staticmethod
    def count_users_by_role(db: Session) -> dict:
        """统计各角色用户数"""
        result = {}
        roles = db.query(Role).all()
        for role in roles:
            count = db.query(User).filter(User.role_id == role.id).count()
            result[role.name] = count
        return result
    
    @staticmethod
    def get_all_roles(db: Session) -> List[Role]:
        """获取所有角色"""
        return db.query(Role).all()
    
    @staticmethod
    def get_role_by_name(db: Session, name: str) -> Optional[Role]:
        """根据名称获取角色"""
        return db.query(Role).filter(Role.name == name).first()
