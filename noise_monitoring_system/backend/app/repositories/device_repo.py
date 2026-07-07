"""
设备数据访问层
"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Device


class DeviceRepository:
    """设备数据访问"""

    @staticmethod
    def get_by_id(db: Session, device_id: int) -> Optional[Device]:
        return db.get(Device, device_id)

    @staticmethod
    def get_by_serial_no(db: Session, serial_no: str) -> Optional[Device]:
        return db.query(Device).filter(Device.serial_no == serial_no).first()

    @staticmethod
    def get_all(db: Session, status: Optional[str] = None) -> List[Device]:
        query = db.query(Device)
        if status:
            query = query.filter(Device.status == status)
        return query.all()

    @staticmethod
    def create(db: Session, device: Device) -> Device:
        db.add(device)
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def update(db: Session, device: Device) -> Device:
        db.commit()
        db.refresh(device)
        return device

    @staticmethod
    def delete(db: Session, device: Device) -> None:
        db.delete(device)
        db.commit()

    @staticmethod
    def count_online(db: Session) -> int:
        """统计在线设备数量"""
        return db.query(Device).filter(Device.status == "active").count()

    @staticmethod
    def count_total(db: Session) -> int:
        """统计设备总数"""
        return db.query(Device).count()

    @staticmethod
    def get_online_rate(db: Session) -> float:
        """计算设备在线率"""
        total = DeviceRepository.count_total(db)
        if total == 0:
            return 0.0
        online = DeviceRepository.count_online(db)
        return round(online / total * 100, 2)
