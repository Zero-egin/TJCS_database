"""
城市声环境治理平台 - FastAPI 入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_router

app = FastAPI(
    title="城市声环境治理平台",
    description="基于 TimescaleDB + PostGIS 的噪声监测与治理系统",
    version="1.0.0"
)

# CORS 配置 (允许前端跨域)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Vite 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok"}

