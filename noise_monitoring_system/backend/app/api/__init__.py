"""
API 路由汇总
"""
from fastapi import APIRouter
from app.api import auth, points, readings, alerts, stats, admin

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(points.router)
api_router.include_router(readings.router)
api_router.include_router(alerts.router)
api_router.include_router(stats.router)
api_router.include_router(admin.router)
