"""
缓存管理模块

提供TTL缓存功能，用于减少重复查询
"""

from cachetools import TTLCache
from typing import Any, Optional, Callable, TypeVar, Dict, Union
from functools import wraps
import asyncio
import logging
import os
import time

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Import Redis cache if available
try:
    from .redis_cache import RedisCacheBackend, FallbackCache, REDIS_AVAILABLE
    REDIS_BACKEND_AVAILABLE = REDIS_AVAILABLE
except ImportError:
    REDIS_BACKEND_AVAILABLE = False
    RedisCacheBackend = None
    FallbackCache = None
    REDIS_AVAILABLE = False


class CacheManager:
    """缓存管理器"""

    def __init__(
        self,
        maxsize: int = 100,
        ttl: int = 1800,
        backend: str = "memory"
    ):
        """
        初始化缓存管理器

        Args:
            maxsize: 最大缓存条目数
            ttl: 生存时间（秒），默认30分钟
            backend: 缓存后端 ("memory" 或 "redis")
        """
        self._cache: TTLCache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._enabled = True
        self._backend_type = backend
        self._redis_backend: Optional["RedisCacheBackend"] = None
        self._fallback_cache: Optional["FallbackCache"] = None

        # 自动清理任务
        self._cleanup_task: Optional[asyncio.Task] = None
        self._cleanup_running = False

        # 统计信息
        self._hits = 0
        self._misses = 0

        # Initialize Redis backend if requested and available
        if backend == "redis" and REDIS_BACKEND_AVAILABLE:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            try:
                self._redis_backend = RedisCacheBackend(url=redis_url)
                logger.info("Redis cache backend initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Redis backend, falling back to memory: {e}")
                self._fallback_cache = FallbackCache(ttl=ttl)
        elif backend == "redis" and not REDIS_BACKEND_AVAILABLE:
            logger.warning("Redis requested but not available, using memory cache")
            self._fallback_cache = FallbackCache(ttl=ttl)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if not self._enabled:
            return None

        # Try Redis backend first
        if self._redis_backend:
            value = self._redis_backend.get(key)
            if value is not None:
                self._hits += 1
            else:
                self._misses += 1
            return value
        elif self._fallback_cache:
            value = self._fallback_cache.get(key)
            if value is not None:
                self._hits += 1
            else:
                self._misses += 1
            return value

        value = self._cache.get(key)
        if value is not None:
            self._hits += 1
        else:
            self._misses += 1
        return value

    async def get_async(self, key: str) -> Optional[Any]:
        """异步获取缓存值"""
        if not self._enabled:
            return None

        if self._redis_backend:
            return await self._redis_backend.get(key)
        elif self._fallback_cache:
            return await self._fallback_cache.get(key)

        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        if not self._enabled:
            return

        if self._redis_backend:
            # Sync fallback for Redis
            try:
                asyncio.create_task(self._redis_backend.set(key, value, ttl))
            except RuntimeError:
                # No event loop
                pass
        elif self._fallback_cache:
            try:
                asyncio.create_task(self._fallback_cache.set(key, value, ttl))
            except RuntimeError:
                pass

        self._cache[key] = value

    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """异步设置缓存值"""
        if not self._enabled:
            return

        if self._redis_backend:
            await self._redis_backend.set(key, value, ttl)
        elif self._fallback_cache:
            await self._fallback_cache.set(key, value, ttl)

        self._cache[key] = value

    def delete(self, key: str) -> None:
        """删除缓存值"""
        if key in self._cache:
            del self._cache[key]

        if self._redis_backend:
            try:
                asyncio.create_task(self._redis_backend.delete(key))
            except RuntimeError:
                pass
        elif self._fallback_cache:
            try:
                asyncio.create_task(self._fallback_cache.delete(key))
            except RuntimeError:
                pass

    async def delete_async(self, key: str) -> None:
        """异步删除缓存值"""
        if key in self._cache:
            del self._cache[key]

        if self._redis_backend:
            await self._redis_backend.delete(key)
        elif self._fallback_cache:
            await self._fallback_cache.delete(key)

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def disable(self) -> None:
        """禁用缓存"""
        self._enabled = False

    def enable(self) -> None:
        """启用缓存"""
        self._enabled = True

    @property
    def size(self) -> int:
        """当前缓存大小"""
        return len(self._cache)

    @property
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_ops = self._hits + self._misses
        hit_rate = self._hits / total_ops if total_ops > 0 else 0

        return {
            "size": len(self._cache),
            "maxsize": self._cache.maxsize,
            "ttl": self._cache.ttl,
            "enabled": self._enabled,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    async def cleanup_expired(self) -> int:
        """
        清理过期的缓存条目

        Returns:
            清理的条目数
        """
        initial_size = len(self._cache)
        # TTLCache会自动清理过期条目，我们只需要触发一次访问
        # 或者我们可以手动检查并删除
        current_time = time.time()
        keys_to_delete = []

        # 由于TTLCache内部使用循环到期，我们通过迭代触发清理
        for key in list(self._cache.keys()):
            try:
                # 尝试访问以触发TTL检查
                _ = self._cache[key]
            except KeyError:
                keys_to_delete.append(key)

        logger.debug(f"Cleaned up {len(keys_to_delete)} expired cache entries")
        return len(keys_to_delete)

    async def start_cleanup_task(
        self,
        interval_seconds: int = 300,
    ) -> None:
        """
        启动自动清理任务

        Args:
            interval_seconds: 清理间隔（秒），默认5分钟
        """
        if self._cleanup_running:
            logger.warning("Cleanup task is already running")
            return

        self._cleanup_running = True

        async def cleanup_loop():
            while self._cleanup_running:
                try:
                    await asyncio.sleep(interval_seconds)
                    if self._cleanup_running:  # 再次检查，避免shutdown后继续执行
                        count = await self.cleanup_expired()
                        if count > 0:
                            logger.info(f"Auto-cleanup: removed {count} expired entries")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")

        self._cleanup_task = asyncio.create_task(cleanup_loop())
        logger.info(f"Started cache cleanup task (interval: {interval_seconds}s)")

    async def stop_cleanup_task(self) -> None:
        """停止自动清理任务"""
        if not self._cleanup_running:
            return

        self._cleanup_running = False

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        self._cleanup_task = None
        logger.info("Stopped cache cleanup task")


# 全局缓存实例
_global_cache: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        # 默认配置
        _global_cache = CacheManager(
            maxsize=100,
            ttl=1800,  # 30分钟
        )
    return _global_cache


def reset_cache() -> None:
    """重置全局缓存"""
    global _global_cache
    _global_cache = None


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None,
):
    """
    缓存装饰器

    Args:
        ttl: 缓存生存时间（秒），None则使用默认值
        key_prefix: 缓存键前缀
        key_builder: 自定义键构建函数，签名为 (func, args, kwargs) -> str

    Usage:
        @cached(ttl=600, key_prefix="project")
        async def get_project(project_id: str):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # 构建缓存键
            if key_builder:
                cache_key = key_builder(func, args, kwargs)
            else:
                # 默认键构建方式
                args_str = ",".join(str(arg) for arg in args)
                kwargs_str = ",".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{func.__name__}:{args_str}:{kwargs_str}"

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 缓存未命中，执行原函数
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


async def cache_invalidate_async(pattern: str = "") -> int:
    """
    使缓存失效（异步版本）

    Args:
        pattern: 键模式，如果提供则只删除匹配的键

    Returns:
        删除的键数量
    """
    cache = get_cache()

    if cache._redis_backend:
        return await cache._redis_backend.invalidate_pattern(pattern)
    elif cache._fallback_cache:
        return await cache._fallback_cache.invalidate_pattern(pattern)

    if pattern:
        # 删除匹配模式的键
        keys_to_delete = [k for k in cache._cache.keys() if pattern in k]
        for key in keys_to_delete:
            cache.delete(key)
        logger.debug(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")
        return len(keys_to_delete)
    else:
        cache.clear()
        logger.debug("Cleared all cache")
        return 0


def cache_invalidate(pattern: str = "") -> None:
    """
    使缓存失效

    Args:
        pattern: 键模式，如果提供则只删除匹配的键
    """
    cache = get_cache()

    if pattern:
        # 删除匹配模式的键
        keys_to_delete = [k for k in cache._cache.keys() if pattern in k]
        for key in keys_to_delete:
            cache.delete(key)
        logger.debug(f"Invalidated {len(keys_to_delete)} cache entries matching '{pattern}'")
    else:
        cache.clear()
        logger.debug("Cleared all cache")


__all__ = [
    "CacheManager",
    "get_cache",
    "reset_cache",
    "cached",
    "cache_invalidate",
    "cache_invalidate_async",
    "RedisCacheBackend",
    "FallbackCache",
    "REDIS_AVAILABLE",
    "REDIS_BACKEND_AVAILABLE",
]
