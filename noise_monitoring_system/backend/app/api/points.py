"""
监测点 API 路由
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import get_db, get_current_active_user, require_super_admin, require_operator_or_admin, require_permission
from app.models import User
from app.schemas import MonitoringPointCreate, MonitoringPointUpdate, MonitoringPointOut
from app.schemas.user import Permission
from app.services import MonitoringPointService

router = APIRouter(prefix="/points", tags=["监测点"])


@router.get("", response_model=List[MonitoringPointOut])
def list_points(
    area_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取监测点列表 (所有用户可访问)"""
    points = MonitoringPointService.get_all_points(db, area_id, status)
    result = []
    for p in points:
        out = MonitoringPointOut.model_validate(p)
        out.area_name = p.area.name if p.area else None
        result.append(out)
    return result


@router.get("/map")
def get_points_for_map(
    reference_time: Optional[datetime] = Query(None, description="历史数据参考时间"),
    db: Session = Depends(get_db)
):
    """获取地图展示数据（含噪声值和状态）
    
    Args:
        reference_time: 可选的历史时间参考点，如果不传则返回最新数据
    """
    return MonitoringPointService.get_points_for_map(db, reference_time)


@router.get("/{point_id}", response_model=MonitoringPointOut)
def get_point(point_id: int, db: Session = Depends(get_db)):
    """获取单个监测点详情 (所有用户可访问)"""
    point = MonitoringPointService.get_point(db, point_id)
    if not point:
        raise HTTPException(status_code=404, detail="监测点不存在")
    out = MonitoringPointOut.model_validate(point)
    out.area_name = point.area.name if point.area else None
    return out


@router.post("", response_model=MonitoringPointOut)
def create_point(
    data: MonitoringPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.POINT_MANAGE))
):
    """创建监测点 (运维员及以上)"""
    point = MonitoringPointService.create_point(db, data)
    return MonitoringPointOut.model_validate(point)


@router.put("/{point_id}", response_model=MonitoringPointOut)
def update_point(
    point_id: int,
    data: MonitoringPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.POINT_MANAGE))
):
    """更新监测点 (运维员及以上)"""
    point = MonitoringPointService.update_point(db, point_id, data)
    if not point:
        raise HTTPException(status_code=404, detail="监测点不存在")
    out = MonitoringPointOut.model_validate(point)
    out.area_name = point.area.name if point.area else None
    return out


@router.delete("/{point_id}")
def delete_point(
    point_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.POINT_MANAGE))
):
    """删除监测点 (运维员及以上)"""
    if not MonitoringPointService.delete_point(db, point_id):
        raise HTTPException(status_code=404, detail="监测点不存在")
    return {"message": "删除成功"}
