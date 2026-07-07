"""
噪声数据 API 路由
"""
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core import get_db, get_current_active_user, require_super_admin, require_operator_or_admin, require_permission
from app.models import User
from app.schemas import NoiseReadingCreate, NoiseReadingOut, IngestionJobOut
from app.schemas.user import Permission
from app.services import NoiseDataService

router = APIRouter(prefix="/readings", tags=["噪声数据"])


@router.post("", response_model=NoiseReadingOut)
def add_reading(
    data: NoiseReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DATA_IMPORT))
):
    """添加单条噪声数据 (运维员及以上)"""
    reading = NoiseDataService.add_reading(db, data)
    return NoiseReadingOut.model_validate(reading)


@router.post("/import", response_model=IngestionJobOut)
async def import_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DATA_IMPORT))
):
    """批量导入 CSV 噪声数据 (运维员及以上)"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="仅支持 CSV 文件")
    
    try:
        job = NoiseDataService.import_from_csv(db, file.file, source=file.filename)
        return IngestionJobOut.model_validate(job)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.get("/history")
def get_history(
    point_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db)
):
    """获取指定点位的历史噪声数据 (所有用户可访问)"""
    readings = NoiseDataService.get_point_history(db, point_id, start_time, end_time)
    return [NoiseReadingOut.model_validate(r) for r in readings]


@router.get("/trend")
def get_trend(
    start_time: datetime = Query(None),
    end_time: datetime = Query(None),
    point_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """获取小时级别噪声趋势 (TimescaleDB time_bucket) (所有用户可访问)"""
    if not start_time:
        start_time = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    if not end_time:
        end_time = datetime.utcnow()
    
    return NoiseDataService.get_hourly_trend(db, start_time, end_time, point_id)


@router.get("/timebucket")
def get_time_bucket_data(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    interval: str = Query("1 hour", description="时间桶间隔，如 '1 hour', '30 minutes'"),
    db: Session = Depends(get_db)
):
    """获取时间桶聚合数据（用于时间轴回溯播放）(所有用户可访问)"""
    return NoiseDataService.get_time_bucket_data(db, start_time, end_time, interval)


@router.delete("/clean")
def clean_error_data(
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    point_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.DATA_CLEAN))
):
    """清理/修正历史错误数据 (仅超级管理员)"""
    count = NoiseDataService.clean_error_data(db, start_time, end_time, point_id)
    return {"message": f"已清理 {count} 条错误数据"}
