"""
认证服务
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import User
from app.repositories import UserRepository


class AuthService:
    """认证服务"""

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """
        验证用户名和密码
        返回 User 对象（如果验证成功）或 None
        注意：此方法只验证用户名和密码，不检查用户状态
        状态检查应该在 API 层进行，以便返回更具体的错误信息
        """
        user = UserRepository.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        # 不再检查状态，让 API 层处理
        return user

    @staticmethod
    def register(db: Session, username: str, password: str, email: Optional[str] = None) -> User:
        """
        注册新用户
        """
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email
        )
        return UserRepository.create(db, user)

    @staticmethod
    def change_password(db: Session, user: User, new_password: str) -> User:
        """
        修改密码
        """
        user.password_hash = hash_password(new_password)
        return UserRepository.update(db, user)

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        验证密码强度
        至少8位，包含字母和数字
        """
        if len(password) < 8:
            return False
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        return has_letter and has_digit
