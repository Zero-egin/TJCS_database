"""
Repository 层基础类和通用导入
"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, TypeVar, Generic, Type

from sqlalchemy import func, text, select, and_, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Base

# 泛型类型变量
T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    通用 Repository 基类
    提供基础 CRUD 操作
    """

    def __init__(self, model: Type[T]):
        self.model = model

    def get_by_id(self, db: Session, id: int) -> Optional[T]:
        return db.get(self.model, id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[T]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, obj: T) -> T:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    def update(self, db: Session, obj: T) -> T:
        db.commit()
        db.refresh(obj)
        return obj

    def delete(self, db: Session, obj: T) -> None:
        db.delete(obj)
        db.commit()

    def count(self, db: Session) -> int:
        return db.query(self.model).count()
