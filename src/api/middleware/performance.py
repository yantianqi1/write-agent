"""
性能监控中间件

提供API响应时间统计、慢查询日志和缓存命中率统计
"""

import time
import logging
from typing import Callable
from functools import wraps
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


# 性能统计
class PerformanceStats:
    """性能统计数据"""

    def __init__(self):
        self.request_counts: defaultdict = defaultdict(int)
        self.request_times: defaultdict = defaultdict(list)
        self.slow_queries: list = []
        self.cache_hits: int = 0
        self.cache_misses: int = 0

    def record_request(self, path: str, method: str, duration: float):
        """记录请求"""
        key = f"{method} {path}"
        self.request_counts[key] += 1
        self.request_times[key].append(duration)

        # 慢查询日志（>1秒）
        if duration > 1.0:
            self.slow_queries.append({
                "path": path,
                "method": method,
                "duration": duration,
                "timestamp": time.time()
            })
            logger.warning(
                f"Slow query detected: {method} {path} took {duration:.2f}s"
            )

    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_hits += 1

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_misses += 1

    def get_stats(self) -> dict:
        """获取统计信息"""
        # 计算平均响应时间
        avg_times = {}
        for key, times in self.request_times.items():
            if times:
                avg_times[key] = sum(times) / len(times)

        # 计算缓存命中率
        total_cache_ops = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            self.cache_hits / total_cache_ops
            if total_cache_ops > 0
            else 0
        )

        return {
            "request_counts": dict(self.request_counts),
            "average_response_times": avg_times,
            "slow_query_count": len(self.slow_queries),
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": cache_hit_rate,
            },
        }


# 全局统计实例
_stats = PerformanceStats()


def get_stats() -> PerformanceStats:
    """获取全局统计实例"""
    return _stats


def reset_stats():
    """重置统计数据"""
    global _stats
    _stats = PerformanceStats()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""

    def __init__(self, app: ASGIApp, slow_query_threshold: float = 1.0):
        """
        初始化性能监控中间件

        Args:
            app: ASGI应用
            slow_query_threshold: 慢查询阈值（秒）
        """
        super().__init__(app)
        self.slow_query_threshold = slow_query_threshold

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()

        # 处理请求
        response = await call_next(request)

        # 计算耗时
        duration = time.time() - start_time

        # 记录统计
        path = request.url.path
        method = request.method
        _stats.record_request(path, method, duration)

        # 添加响应头
        response.headers["X-Response-Time"] = f"{duration:.3f}s"

        return response


def timing_decorator(func: Callable) -> Callable:
    """
    函数计时装饰器

    Usage:
        @timing_decorator
        async def my_function():
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start_time
            logger.debug(f"{func.__name__} took {duration:.3f}s")
            if duration > 1.0:
                logger.warning(
                    f"Slow function call: {func.__name__} took {duration:.2f}s"
                )
    return wrapper


def track_cache_hit(func: Callable) -> Callable:
    """
    缓存命中追踪装饰器

    Usage:
        @track_cache_hit
        async def get_cached_data(key):
            ...
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        result = await func(*args, **kwargs)
        # 假设返回None表示缓存未命中
        if result is not None:
            _stats.record_cache_hit()
        else:
            _stats.record_cache_miss()
        return result
    return wrapper


def add_timing_middleware(app, slow_query_threshold: float = 1.0):
    """
   添加性能监控中间件到FastAPI应用

    Args:
        app: FastAPI应用实例
        slow_query_threshold: 慢查询阈值（秒）
    """
    app.add_middleware(PerformanceMiddleware, slow_query_threshold=slow_query_threshold)


__all__ = [
    "PerformanceMiddleware",
    "add_timing_middleware",
    "timing_decorator",
    "track_cache_hit",
    "get_stats",
    "reset_stats",
]
