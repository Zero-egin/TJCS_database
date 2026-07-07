"""
数据导入任务数据访问层
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import IngestionJob


class IngestionJobRepository:
    """数据导入任务数据访问"""

    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Optional[IngestionJob]:
        return db.get(IngestionJob, job_id)

    @staticmethod
    def create(db: Session, job: IngestionJob) -> IngestionJob:
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def update(db: Session, job: IngestionJob) -> IngestionJob:
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[IngestionJob]:
        return db.query(IngestionJob)\
            .order_by(IngestionJob.id.desc())\
            .offset(skip)\
            .limit(limit)\
            .all()

    @staticmethod
    def get_by_status(db: Session, status: str) -> List[IngestionJob]:
        return db.query(IngestionJob)\
            .filter(IngestionJob.status == status)\
            .order_by(IngestionJob.id.desc())\
            .all()

    @staticmethod
    def count(db: Session) -> int:
        return db.query(IngestionJob).count()

    @staticmethod
    def count_by_status(db: Session, status: str) -> int:
        return db.query(IngestionJob).filter(IngestionJob.status == status).count()
