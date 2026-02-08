"""
速率限制中间件

使用滑动窗口算法实现API速率限制
"""

import time
import asyncio
import logging
from collections import defaultdict, deque
from typing import Optional, Dict, Tuple
from datetime import datetime

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    滑动窗口速率限制器

    使用时间窗口内的请求时间戳队列来跟踪请求频率
    """

    def __init__(self, max_requests: int, window_seconds: int = 60):
        """
        初始化速率限制器

        Args:
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口大小（秒），默认60秒
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # {identifier: deque([timestamp1, timestamp2, ...])}
        self._requests: Dict[str, deque] = defaultdict(lambda: deque())
        self._lock = asyncio.Lock()

    async def is_allowed(
        self,
        identifier: str,
        current_time: Optional[float] = None,
    ) -> Tuple[bool, int, int]:
        """
        检查请求是否允许

        Args:
            identifier: 唯一标识符（IP地址、用户ID等）
            current_time: 当前时间戳，用于测试

        Returns:
            (是否允许, 剩余请求数, 重置时间)
        """
        if current_time is None:
            current_time = time.time()

        async with self._lock:
            requests = self._requests[identifier]

            # 移除窗口外的旧请求
            cutoff_time = current_time - self.window_seconds
            while requests and requests[0] <= cutoff_time:
                requests.popleft()

            # 检查是否超过限制
            if len(requests) >= self.max_requests:
                # 计算最旧请求的过期时间
                reset_time = int(requests[0] + self.window_seconds)
                remaining = 0
                return False, remaining, reset_time

            # 记录新请求
            requests.append(current_time)
            remaining = self.max_requests - len(requests)
            reset_time = int(current_time + self.window_seconds)

            return True, remaining, reset_time

    def get_usage(self, identifier: str) -> Tuple[int, int]:
        """
        获取当前使用情况

        Args:
            identifier: 唯一标识符

        Returns:
            (已使用请求数, 最大请求数)
        """
        requests = self._requests[identifier]
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds

        # 清理旧请求
        while requests and requests[0] <= cutoff_time:
            requests.popleft()

        return len(requests), self.max_requests

    async def reset(self, identifier: str):
        """重置指定标识符的计数"""
        async with self._lock:
            if identifier in self._requests:
                del self._requests[identifier]

    async def clear(self):
        """清空所有计数"""
        async with self._lock:
            self._requests.clear()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    全局限流中间件

    默认限制：60请求/分钟
    可针对不同路径配置不同限制
    """

    # 默认限制
    DEFAULT_LIMIT = 60  # 请求/分钟

    # 各端点的特定限制
    PATH_LIMITS = {
        "/api/chat": 30,  # 聊天API: 30请求/分钟
        "/api/generate": 10,  # 生成API: 10请求/分钟
    }

    # 管理员/信任用户的白名单（IP或用户ID）
    WHITELIST = set()

    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = DEFAULT_LIMIT,
        path_limits: Optional[Dict[str, int]] = None,
        whitelist: Optional[set] = None,
    ):
        """
        初始化限流中间件

        Args:
            app: ASGI应用
            default_limit: 默认限制（请求数/分钟）
            path_limits: 各路径的特定限制
            whitelist: 白名单集合（IP或用户ID）
        """
        super().__init__(app)
        self.default_limit = default_limit
        self.path_limits = {**self.PATH_LIMITS, **(path_limits or {})}
        self.whitelist = whitelist or self.WHITELIST

        # 创建不同限制的限流器
        self._limiters: Dict[int, RateLimiter] = {}

    def _get_limiter(self, limit: int) -> RateLimiter:
        """获取或创建指定限制的限流器"""
        if limit not in self._limiters:
            self._limiters[limit] = RateLimiter(max_requests=limit, window_seconds=60)
        return self._limiters[limit]

    def _get_limit_for_path(self, path: str) -> int:
        """获取指定路径的限制"""
        # 精确匹配
        if path in self.path_limits:
            return self.path_limits[path]

        # 前缀匹配
        for prefix, limit in self.path_limits.items():
            if path.startswith(prefix):
                return limit

        return self.default_limit

    def _get_identifier(self, request: Request) -> str:
        """
        获取请求的唯一标识符

        优先级:
        1. 用户ID（如果已认证）
        2. API Key
        3. IP地址
        """
        # 尝试从请求state获取用户
        if hasattr(request.state, "user") and request.state.user:
            user_id = request.state.user.get("id")
            if user_id:
                return f"user:{user_id}"

        # 尝试API Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"apikey:{api_key}"

        # 使用IP地址
        # 转发代理的情况，从 X-Forwarded-For 获取真实IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    async def dispatch(self, request: Request, call_next):
        """
        处理请求，检查速率限制

        返回:
            - 429 Too Many Requests 当超过限制时
            - 添加速率限制响应头:
                - X-RateLimit-Limit: 限制总数
                - X-RateLimit-Remaining: 剩余请求数
                - X-RateLimit-Reset: 重置时间戳
        """
        path = request.url.path

        # 跳过健康检查和文档路径
        if path in ["/", "/health", "/docs", "/redoc", "/openapi.json", "/api/health"]:
            return await call_next(request)

        # 获取标识符
        identifier = self._get_identifier(request)

        # 检查白名单
        if identifier in self.whitelist:
            return await call_next(request)

        # 获取该路径的限制
        limit = self._get_limit_for_path(path)

        # 检查是否允许
        limiter = self._get_limiter(limit)
        allowed, remaining, reset_time = await limiter.is_allowed(identifier)

        # 添加响应头
        headers = {
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }

        if not allowed:
            logger.info(
                f"Rate limit exceeded for {identifier} on {path}: "
                f"{remaining}/{limit} requests"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Rate limit exceeded. Try again in {reset_time - int(time.time())} seconds.",
                    "retry_after": reset_time - int(time.time()),
                },
                headers={
                    **headers,
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )

        # 继续处理请求
        response = await call_next(request)

        # 添加速率限制响应头
        for key, value in headers.items():
            response.headers[key] = value

        return response


class TokenBucketRateLimiter:
    """
    令牌桶算法速率限制器

    适合处理突发流量
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        初始化令牌桶限流器

        Args:
            capacity: 桶容量（最大令牌数）
            refill_rate: 填充速率（令牌/秒）
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self._tokens: Dict[str, float] = defaultdict(lambda: float(capacity))
        self._last_update: Dict[str, float] = defaultdict(time.time)
        self._lock = asyncio.Lock()

    async def consume(self, identifier: str, tokens: int = 1) -> Tuple[bool, float]:
        """
        消费令牌

        Args:
            identifier: 唯一标识符
            tokens: 需要消费的令牌数

        Returns:
            (是否成功, 预计等待时间)
        """
        async with self._lock:
            now = time.time()
            last_time = self._last_update[identifier]

            # 计算新令牌数
            elapsed = now - last_time
            current_tokens = self._tokens[identifier]
            new_tokens = min(
                self.capacity,
                current_tokens + elapsed * self.refill_rate
            )

            # 检查是否有足够令牌
            if new_tokens < tokens:
                wait_time = (tokens - new_tokens) / self.refill_rate
                return False, wait_time

            # 消费令牌
            self._tokens[identifier] = new_tokens - tokens
            self._last_update[identifier] = now
            return True, 0


class RateLimitExceeded(HTTPException):
    """
    速率限制异常

    可在路由中抛出此异常来自动触发限流响应
    """

    def __init__(
        self,
        retry_after: int = 60,
        detail: str = "Rate limit exceeded",
    ):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )
        self.retry_after = retry_after


__all__ = [
    "RateLimiter",
    "RateLimitMiddleware",
    "TokenBucketRateLimiter",
    "RateLimitExceeded",
]
