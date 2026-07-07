"""
报警 API 路由
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import get_db, get_current_active_user, require_super_admin, require_operator_or_admin, require_permission
from app.models import User
from app.schemas import AlertOut, AlertResolve, PaginatedResponse
from app.schemas.user import Permission
from app.repositories import AlertRepository
from app.services import AlertService

router = APIRouter(prefix="/alerts", tags=["报警"])


@router.get("")
def list_alerts(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    area_type: Optional[str] = Query(None, description="区域类别: residential/commercial/industrial/mixed"),
    min_level: Optional[int] = Query(None, description="最低分贝阈值: 50/60/70"),
    status: Optional[str] = Query(None, description="状态: open/resolved"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取报警列表（支持多维联动筛选）(所有登录用户可查看)"""
    # 使用 skip 和 limit 直接查询
    alerts, total = AlertRepository.get_all(
        db,
        start_time=start_time,
        end_time=end_time,
        area_type=area_type,
        status=status,
        skip=skip,
        limit=limit
    )
    
    result = []
    for alert in alerts:
        out = AlertOut.model_validate(alert)
        out.point_name = alert.point.name if alert.point else None
        out.area_type = alert.point.area.type if alert.point and alert.point.area else None
        out.latitude = alert.point.latitude if alert.point else None
        out.longitude = alert.point.longitude if alert.point else None
        out.handler = alert.resolved_by  # 处置人
        out.resolved_by_name = alert.resolved_by
        result.append(out)
    
    return {
        "code": 0,
        "message": "success",
        "total": total,
        "items": result
    }


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个报警详情 (所有登录用户可查看)"""
    alert = AlertService.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="报警不存在")
    out = AlertOut.model_validate(alert)
    out.point_name = alert.point.name if alert.point else None
    out.area_type = alert.point.area.type if alert.point and alert.point.area else None
    out.latitude = alert.point.latitude if alert.point else None
    out.longitude = alert.point.longitude if alert.point else None
    return out


@router.post("/{alert_id}/resolve", response_model=AlertOut)
def resolve_alert(
    alert_id: int,
    data: AlertResolve,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ALERT_RESOLVE))
):
    """处置报警 (运维员及以上)"""
    alert = AlertService.resolve_alert(db, alert_id, current_user.id, data.notes, data.handler)
    if not alert:
        raise HTTPException(status_code=404, detail="报警不存在")
    out = AlertOut.model_validate(alert)
    out.point_name = alert.point.name if alert.point else None
    out.handler = alert.resolved_by  # 返回处置人
    out.resolved_by_name = alert.resolved_by
    return out


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ALERT_MANAGE))
):
    """删除/归档报警记录 (仅超级管理员)"""
    if not AlertService.delete_alert(db, alert_id):
        raise HTTPException(status_code=404, detail="报警不存在")
    return {"message": "删除成功"}


@router.post("/{alert_id}/archive")
def archive_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.ALERT_MANAGE))
):
    """归档报警记录 (仅超级管理员)"""
    alert = AlertService.archive_alert(db, alert_id, user_id=current_user.id)
    if not alert:
        raise HTTPException(status_code=404, detail="报警不存在")
    return {"message": "归档成功"}
