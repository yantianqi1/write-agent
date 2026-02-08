"""
API中间件模块
"""

from .performance import PerformanceMiddleware, add_timing_middleware
from .auth import (
    AuthMiddleware,
    create_access_token,
    decode_token,
    get_current_user,
    require_auth,
)
from .rate_limit import RateLimitMiddleware, RateLimiter
from .validation import (
    InputValidator,
    ValidationMiddleware,
    SecurityHeadersMiddleware,
    ContentLengthMiddleware,
)
from .monitoring import (
    PerformanceMetrics,
    MonitoringMiddleware,
    get_metrics,
    reset_metrics,
    start_background_sampler,
)

__all__ = [
    # Performance
    "PerformanceMiddleware",
    "add_timing_middleware",
    # Auth
    "AuthMiddleware",
    "create_access_token",
    "decode_token",
    "get_current_user",
    "require_auth",
    # Rate Limit
    "RateLimitMiddleware",
    "RateLimiter",
    # Validation & Security
    "InputValidator",
    "ValidationMiddleware",
    "SecurityHeadersMiddleware",
    "ContentLengthMiddleware",
    # Monitoring
    "PerformanceMetrics",
    "MonitoringMiddleware",
    "get_metrics",
    "reset_metrics",
    "start_background_sampler",
]
