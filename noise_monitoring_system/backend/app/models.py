"""
数据模型层 (Models / Persistence Layer)
使用 SQLAlchemy ORM 定义与数据库表对应的实体类
支持 PostGIS 空间类型 (via GeoAlchemy2) 和 TimescaleDB 时序表
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


# ==================== 用户与权限 ====================
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(120))
    phone: Mapped[Optional[str]] = mapped_column(String(20))
    real_name: Mapped[Optional[str]] = mapped_column(String(50))
    role_id: Mapped[Optional[int]] = mapped_column(ForeignKey("roles.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    role: Mapped[Optional["Role"]] = relationship(back_populates="users")
    actions: Mapped[list["Action"]] = relationship(back_populates="user")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user")


# ==================== 区域 ====================
class Area(Base):
    __tablename__ = "areas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[Optional[str]] = mapped_column(String(50))  # residential, commercial, industrial, mixed
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    # PostGIS geometry column (generated in DB, read-only here)
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=True)

    monitoring_points: Mapped[list["MonitoringPoint"]] = relationship(back_populates="area")
    threshold_rules: Mapped[list["ThresholdRule"]] = relationship(back_populates="area")

    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_areas_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_areas_longitude"),
    )


# ==================== 设备 ====================
class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    serial_no: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model: Mapped[Optional[str]] = mapped_column(String(100))
    installed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(20), default="active")

    monitoring_points: Mapped[list["MonitoringPoint"]] = relationship(back_populates="device")
    noise_readings: Mapped[list["NoiseReading"]] = relationship(back_populates="device")


# ==================== 监测点 ====================
class MonitoringPoint(Base):
    __tablename__ = "monitoring_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id", ondelete="SET NULL"))
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6))
    geom = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    threshold_db: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("65.00"))
    status: Mapped[str] = mapped_column(String(20), default="active")

    area: Mapped[Optional["Area"]] = relationship(back_populates="monitoring_points")
    device: Mapped[Optional["Device"]] = relationship(back_populates="monitoring_points")
    noise_readings: Mapped[list["NoiseReading"]] = relationship(back_populates="point")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="point")
    threshold_rules: Mapped[list["ThresholdRule"]] = relationship(back_populates="point")

    __table_args__ = (
        CheckConstraint("latitude BETWEEN -90 AND 90", name="ck_points_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="ck_points_longitude"),
        CheckConstraint("threshold_db BETWEEN 0 AND 200", name="ck_points_threshold"),
    )


# ==================== 噪声数据 (TimescaleDB Hypertable) ====================
class NoiseReading(Base):
    __tablename__ = "noise_readings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    point_id: Mapped[int] = mapped_column(ForeignKey("monitoring_points.id", ondelete="CASCADE"), nullable=False)
    device_id: Mapped[Optional[int]] = mapped_column(ForeignKey("devices.id"))
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    db_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    temperature: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    humidity: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    battery_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    is_exceed: Mapped[bool] = mapped_column(Boolean, default=False)

    point: Mapped["MonitoringPoint"] = relationship(back_populates="noise_readings")
    device: Mapped[Optional["Device"]] = relationship(back_populates="noise_readings")

    __table_args__ = (
        CheckConstraint("db_value BETWEEN 0 AND 200", name="ck_readings_db_value"),
    )


# ==================== 报警 ====================
class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reading_id: Mapped[Optional[int]] = mapped_column(BigInteger)
    point_id: Mapped[int] = mapped_column(ForeignKey("monitoring_points.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), default="threshold")  # threshold, anomaly, trend
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # low, medium, high, critical
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    db_value: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    threshold_db: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, acknowledged, resolved, dismissed, archived
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    resolved_by: Mapped[Optional[str]] = mapped_column(String(100))  # 处置人名称
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    point: Mapped["MonitoringPoint"] = relationship(back_populates="alerts")
    actions: Mapped[list["Action"]] = relationship(back_populates="alert")


# ==================== 阈值规则 ====================
class ThresholdRule(Base):
    __tablename__ = "threshold_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    area_id: Mapped[Optional[int]] = mapped_column(ForeignKey("areas.id", ondelete="SET NULL"))
    point_id: Mapped[Optional[int]] = mapped_column(ForeignKey("monitoring_points.id", ondelete="SET NULL"))
    day_of_week: Mapped[Optional[int]] = mapped_column(Integer)  # 0-6 (Sunday-Saturday)
    time_range: Mapped[Optional[str]] = mapped_column(String(20))  # e.g., "08:00-22:00"
    threshold_db: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    area: Mapped[Optional["Area"]] = relationship(back_populates="threshold_rules")
    point: Mapped[Optional["MonitoringPoint"]] = relationship(back_populates="threshold_rules")

    __table_args__ = (
        CheckConstraint("threshold_db BETWEEN 0 AND 200", name="ck_rules_threshold"),
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="ck_rules_dow"),
    )


# ==================== 处置动作 ====================
class Action(Base):
    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    action_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    alert: Mapped["Alert"] = relationship(back_populates="actions")
    user: Mapped[Optional["User"]] = relationship(back_populates="actions")


# ==================== 数据导入任务 ====================
class IngestionJob(Base):
    __tablename__ = "ingestion_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[Optional[str]] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, running, success, failed
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    records_count: Mapped[int] = mapped_column(Integer, default=0)


# ==================== 审计日志 ====================
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship(back_populates="audit_logs")
