"""
阈值规则数据访问层
"""
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import ThresholdRule, Area, MonitoringPoint


class ThresholdRuleRepository:
    """阈值规则数据访问"""

    @staticmethod
    def get_by_id(db: Session, rule_id: int) -> Optional[ThresholdRule]:
        return db.query(ThresholdRule)\
            .options(
                joinedload(ThresholdRule.area),
                joinedload(ThresholdRule.point)
            )\
            .filter(ThresholdRule.id == rule_id)\
            .first()

    @staticmethod
    def get_all(db: Session, is_active: Optional[bool] = None) -> List[ThresholdRule]:
        query = db.query(ThresholdRule).options(
            joinedload(ThresholdRule.area),
            joinedload(ThresholdRule.point)
        )
        if is_active is not None:
            query = query.filter(ThresholdRule.is_active == is_active)
        return query.all()

    @staticmethod
    def get_by_area(db: Session, area_id: int) -> List[ThresholdRule]:
        return db.query(ThresholdRule)\
            .filter(ThresholdRule.area_id == area_id)\
            .all()

    @staticmethod
    def get_by_point(db: Session, point_id: int) -> Optional[ThresholdRule]:
        return db.query(ThresholdRule)\
            .filter(ThresholdRule.point_id == point_id)\
            .first()

    @staticmethod
    def create(db: Session, rule: ThresholdRule) -> ThresholdRule:
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def update(db: Session, rule: ThresholdRule) -> ThresholdRule:
        db.commit()
        db.refresh(rule)
        return rule

    @staticmethod
    def delete(db: Session, rule: ThresholdRule) -> None:
        db.delete(rule)
        db.commit()

    @staticmethod
    def get_effective_threshold(db: Session, point_id: int, area_id: Optional[int]) -> Optional[ThresholdRule]:
        """
        获取生效的阈值规则
        优先级: 监测点级别 > 区域级别 > 全局默认
        """
        # 先查找监测点级别规则
        rule = db.query(ThresholdRule)\
            .filter(
                ThresholdRule.point_id == point_id,
                ThresholdRule.is_active == True
            ).first()
        if rule:
            return rule
        
        # 再查找区域级别规则
        if area_id:
            rule = db.query(ThresholdRule)\
                .filter(
                    ThresholdRule.area_id == area_id,
                    ThresholdRule.point_id == None,
                    ThresholdRule.is_active == True
                ).first()
            if rule:
                return rule
        
        # 最后查找全局默认规则
        return db.query(ThresholdRule)\
            .filter(
                ThresholdRule.area_id == None,
                ThresholdRule.point_id == None,
                ThresholdRule.is_active == True
            ).first()
