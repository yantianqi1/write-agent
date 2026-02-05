"""
API路由模块
"""

from .chat import router as chat_router
from .projects import router as projects_router
from .generation import router as generation_router
from .health import router as health_router

__all__ = [
    "chat_router",
    "projects_router",
    "generation_router",
    "health_router",
]
