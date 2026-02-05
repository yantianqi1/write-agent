"""
健康检查路由
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    version: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        service="WriteAgent API"
    )


@router.get("/")
async def root():
    """根路径"""
    return {
        "service": "WriteAgent API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs"
    }
