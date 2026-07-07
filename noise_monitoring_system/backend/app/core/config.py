"""
应用配置
从环境变量或 .env 文件加载配置
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)


# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres123@localhost:5432/noise_db",
)

# JWT 配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24小时

# CORS 配置
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

# 调试模式
DEBUG = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

# 日志级别
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
