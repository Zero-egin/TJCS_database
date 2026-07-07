"""
通用 Schema 定义
"""
from pydantic import BaseModel


class ResponseBase(BaseModel):
    """通用响应基类"""
    code: int = 0
    message: str = "success"


class PaginatedResponse(ResponseBase):
    """分页响应基类"""
    total: int
    page: int
    page_size: int
