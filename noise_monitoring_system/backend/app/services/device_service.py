"""
设备管理服务
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import Device
from app.repositories import DeviceRepository
from app.schemas import DeviceCreate, DeviceUpdate


class DeviceService:
    """设备管理服务"""

    @staticmethod
    def create_device(db: Session, data: DeviceCreate) -> Device:
        """创建设备"""
        device = Device(
            serial_no=data.serial_no,
            model=data.model,
            status=data.status or "active",
            installed_at=datetime.utcnow()
        )
        return DeviceRepository.create(db, device)

    @staticmethod
    def get_device(db: Session, device_id: int) -> Optional[Device]:
        """获取设备"""
        return DeviceRepository.get_by_id(db, device_id)

    @staticmethod
    def get_device_by_serial(db: Session, serial_no: str) -> Optional[Device]:
        """根据序列号获取设备"""
        return DeviceRepository.get_by_serial_no(db, serial_no)

    @staticmethod
    def get_all_devices(db: Session, status: Optional[str] = None) -> List[Device]:
        """获取所有设备"""
        return DeviceRepository.get_all(db, status)

    @staticmethod
    def update_device(
        db: Session, 
        device_id: int, 
        data: DeviceUpdate
    ) -> Optional[Device]:
        """更新设备"""
        device = DeviceRepository.get_by_id(db, device_id)
        if not device:
            return None
        if data.model is not None:
            device.model = data.model
        if data.status is not None:
            device.status = data.status
        if data.serial_no is not None:
            device.serial_no = data.serial_no
        return DeviceRepository.update(db, device)

    @staticmethod
    def delete_device(db: Session, device_id: int) -> bool:
        """删除设备"""
        device = DeviceRepository.get_by_id(db, device_id)
        if not device:
            return False
        DeviceRepository.delete(db, device)
        return True

    @staticmethod
    def activate_device(db: Session, device_id: int) -> Optional[Device]:
        """激活设备"""
        device = DeviceRepository.get_by_id(db, device_id)
        if not device:
            return None
        device.status = "active"
        return DeviceRepository.update(db, device)

    @staticmethod
    def deactivate_device(db: Session, device_id: int) -> Optional[Device]:
        """停用设备"""
        device = DeviceRepository.get_by_id(db, device_id)
        if not device:
            return None
        device.status = "inactive"
        return DeviceRepository.update(db, device)

    @staticmethod
    def get_online_rate(db: Session) -> Decimal:
        """计算设备在线率"""
        total = DeviceRepository.count_total(db)
        if total == 0:
            return Decimal("0")
        online = DeviceRepository.count_online(db)
        return round(Decimal(online) / Decimal(total) * 100, 2)

    @staticmethod
    def count_devices(db: Session) -> int:
        """统计设备总数"""
        return DeviceRepository.count_total(db)

    @staticmethod
    def count_online_devices(db: Session) -> int:
        """统计在线设备数"""
        return DeviceRepository.count_online(db)
