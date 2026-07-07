"""
用户数据访问层
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    """用户数据访问"""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        return db.get(User, user_id)

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, user: User) -> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update(db: Session, user: User) -> User:
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user: User) -> None:
        """删除用户，使用原生 SQL 确保外键约束正确处理"""
        from sqlalchemy import text
        user_id = user.id
        try:
            # 使用原生 SQL 删除，数据库会自动处理 ON DELETE SET NULL
            db.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def count(db: Session) -> int:
        return db.query(User).count()

    @staticmethod
    def count_active(db: Session) -> int:
        return db.query(User).filter(User.status == "active").count()
