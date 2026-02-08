"""
缓存装饰器

提供便捷的缓存装饰器函数
"""

from typing import Optional, Callable, Any
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def async_cached(
    cache_getter: Callable,
    key_builder: Callable,
    ttl: Optional[int] = None,
):
    """
    异步缓存装饰器

    Args:
        cache_getter: 获取缓存实例的函数
        key_builder: 构建缓存键的函数
        ttl: 缓存生存时间

    Usage:
        @async_cached(
            cache_getter=lambda: get_cache(),
            key_builder=lambda self, project_id: f"project:{project_id}",
            ttl=600
        )
        async def get_project(self, project_id: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache = cache_getter()

            # 构建缓存键
            cache_key = key_builder(*args, **kwargs)

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # 执行原函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def cached_result(
    cache_key: str,
    ttl: int = 300,
):
    """
    简单的结果缓存装饰器

    Args:
        cache_key: 固定的缓存键
        ttl: 缓存生存时间（秒）

    Usage:
        @cached_result("all_projects", ttl=60)
        async def list_all_projects():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            from . import get_cache
            cache = get_cache()

            # 尝试从缓存获取
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # 执行原函数
            result = await func(*args, **kwargs)

            # 存入缓存
            cache.set(cache_key, result)

            return result

        return wrapper

    return decorator


def invalidate_on_success(
    *invalidate_keys: str,
):
    """
    函数成功执行后使指定缓存失效

    Args:
        *invalidate_keys: 要失效的缓存键

    Usage:
        @invalidate_on_success("all_projects", "project:{project_id}")
        async def update_project(project_id: str, ...):
            # 在函数内部，可以通过 project_id 格式化键
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            from . import get_cache
            cache = get_cache()

            result = await func(*args, **kwargs)

            # 使缓存失效
            for key_pattern in invalidate_keys:
                # 尝试格式化键
                try:
                    formatted_key = key_pattern.format(**kwargs)
                    cache.delete(formatted_key)
                except (KeyError, AttributeError):
                    cache.delete(key_pattern)

            return result

        return wrapper

    return decorator


__all__ = [
    "async_cached",
    "cached_result",
    "invalidate_on_success",
]
