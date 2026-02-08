"""
LLM调用超时和重试机制

提供带超时和重试的LLM调用装饰器
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, TypeVar, Coroutine
from datetime import datetime

logger = logging.getLogger(__name__)

T = TypeVar('T')


class LLMTimeoutError(Exception):
    """LLM调用超时异常"""
    def __init__(self, timeout: float, message: str = "LLM call timed out"):
        self.timeout = timeout
        super().__init__(message)


class LLMRateLimitError(Exception):
    """LLM速率限制异常"""
    def __init__(self, retry_after: Optional[float] = None, message: str = "LLM rate limit exceeded"):
        self.retry_after = retry_after
        super().__init__(message)


class LLMConnectionError(Exception):
    """LLM连接异常"""
    pass


class LLMInvalidResponseError(Exception):
    """LLM响应无效异常"""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    判断错误是否可重试

    Args:
        error: 异常对象

    Returns:
        是否可重试
    """
    # 网络相关错误可重试
    if isinstance(error, (LLMConnectionError, LLMTimeoutError)):
        return True

    # 速率限制错误可重试
    if isinstance(error, LLMRateLimitError):
        return True

    # 检查错误消息中的关键词
    error_msg = str(error).lower()
    retryable_keywords = [
        "timeout",
        "connection",
        "network",
        "temporary",
        "rate limit",
        "429",  # HTTP 429 Too Many Requests
        "503",  # HTTP 503 Service Unavailable
        "502",  # HTTP 502 Bad Gateway
        "504",  # HTTP 504 Gateway Timeout
    ]

    return any(keyword in error_msg for keyword in retryable_keywords)


def with_llm_retry(
    max_retries: int = 3,
    timeout: float = 60.0,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_backoff: bool = True,
    jitter: bool = True,
):
    """
    LLM调用重试装饰器（同步版本）

    Args:
        max_retries: 最大重试次数
        timeout: 超时时间（秒）
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        exponential_backoff: 是否使用指数退避
        jitter: 是否添加随机抖动

    Usage:
        @with_llm_retry(max_retries=3, timeout=60)
        def call_llm(prompt: str) -> str:
            return llm.generate(prompt)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries):
                try:
                    # 使用超时执行
                    if asyncio.iscoroutinefunction(func):
                        # 异步函数处理
                        return asyncio.run(_execute_with_timeout_async(
                            func, args, kwargs, timeout
                        ))
                    else:
                        # 同步函数处理
                        return _execute_with_timeout(
                            func, args, kwargs, timeout
                        )

                except Exception as e:
                    last_exception = e

                    # 检查是否可重试
                    if not is_retryable_error(e):
                        logger.warning(f"LLM call failed with non-retryable error: {e}")
                        raise

                    # 如果是最后一次尝试，直接抛出异常
                    if attempt >= max_retries - 1:
                        logger.error(
                            f"LLM call failed after {max_retries} attempts: {e}"
                        )
                        raise

                    # 计算延迟时间
                    current_delay = min(delay, max_delay)

                    # 添加抖动
                    if jitter:
                        import random
                        current_delay = current_delay * (0.5 + random.random())

                    logger.info(
                        f"LLM call attempt {attempt + 1} failed: {e}. "
                        f"Retrying in {current_delay:.2f}s..."
                    )

                    import time
                    time.sleep(current_delay)

                    # 更新延迟时间（指数退避）
                    if exponential_backoff:
                        delay = base_delay * (2 ** (attempt + 1))

            # 理论上不会到达这里，但为了类型安全
            raise last_exception

        return wrapper
    return decorator


async def _execute_with_timeout_async(
    func: Callable,
    args: tuple,
    kwargs: dict,
    timeout: float,
) -> Any:
    """异步执行带超时"""
    try:
        return await asyncio.wait_for(
            func(*args, **kwargs),
            timeout=timeout,
        )
    except asyncio.TimeoutError:
        raise LLMTimeoutError(timeout)


def _execute_with_timeout(
    func: Callable,
    args: tuple,
    kwargs: dict,
    timeout: float,
) -> Any:
    """同步执行带超时"""
    # 对于同步函数，我们直接调用，超时由调用方控制
    # 或者可以使用线程池实现真正的超时
    try:
        result = func(*args, **kwargs)
        # 如果返回的是协程对象，等待它
        if asyncio.iscoroutine(result):
            return asyncio.run(asyncio.wait_for(result, timeout=timeout))
        return result
    except asyncio.TimeoutError:
        raise LLMTimeoutError(timeout)


def with_async_llm_retry(
    max_retries: int = 3,
    timeout: float = 60.0,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    exponential_backoff: bool = True,
    jitter: bool = True,
):
    """
    LLM调用重试装饰器（异步版本）

    用于装饰异步LLM调用函数

    Usage:
        @with_async_llm_retry(max_retries=3, timeout=60)
        async def call_llm_async(prompt: str) -> str:
            return await llm.generate_async(prompt)
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]) -> Callable[..., Coroutine[Any, Any, T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            delay = base_delay

            for attempt in range(max_retries):
                try:
                    # 使用超时执行
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout,
                    )

                except asyncio.TimeoutError as e:
                    last_exception = LLMTimeoutError(timeout)
                    logger.warning(
                        f"LLM call attempt {attempt + 1} timed out after {timeout}s"
                    )

                except Exception as e:
                    last_exception = e

                    # 检查是否可重试
                    if not is_retryable_error(e):
                        logger.warning(f"LLM call failed with non-retryable error: {e}")
                        raise

                    logger.warning(
                        f"LLM call attempt {attempt + 1} failed: {e}"
                    )

                # 如果是最后一次尝试，直接抛出异常
                if attempt >= max_retries - 1:
                    logger.error(
                        f"LLM call failed after {max_retries} attempts"
                    )
                    raise last_exception

                # 计算延迟时间
                current_delay = min(delay, max_delay)

                # 添加抖动
                if jitter:
                    import random
                    current_delay = current_delay * (0.5 + random.random())

                logger.info(
                    f"Retrying LLM call in {current_delay:.2f}s... "
                    f"(attempt {attempt + 2}/{max_retries})"
                )

                await asyncio.sleep(current_delay)

                # 更新延迟时间（指数退避）
                if exponential_backoff:
                    delay = base_delay * (2 ** (attempt + 1))

            # 理论上不会到达这里
            raise last_exception

        return wrapper
    return decorator


class LLMRetryTracker:
    """
    LLM重试统计跟踪器

    记录重试次数、成功率等指标
    """

    def __init__(self):
        self._call_counts: dict[str, int] = {}
        self._retry_counts: dict[str, int] = {}
        self._success_counts: dict[str, int] = {}
        self._failure_counts: dict[str, int] = {}
        self._total_time: dict[str, float] = {}

    def record_call(self, operation: str, retries: int, success: bool, duration: float):
        """记录一次LLM调用"""
        if operation not in self._call_counts:
            self._call_counts[operation] = 0
            self._retry_counts[operation] = 0
            self._success_counts[operation] = 0
            self._failure_counts[operation] = 0
            self._total_time[operation] = 0.0

        self._call_counts[operation] += 1
        self._retry_counts[operation] += retries
        self._total_time[operation] += duration

        if success:
            self._success_counts[operation] += 1
        else:
            self._failure_counts[operation] += 1

    def get_stats(self, operation: Optional[str] = None) -> dict:
        """获取统计信息"""
        if operation:
            if operation not in self._call_counts:
                return {}
            return {
                "operation": operation,
                "total_calls": self._call_counts[operation],
                "total_retries": self._retry_counts[operation],
                "success_count": self._success_counts[operation],
                "failure_count": self._failure_counts[operation],
                "success_rate": (
                    self._success_counts[operation] / self._call_counts[operation]
                    if self._call_counts[operation] > 0 else 0
                ),
                "avg_duration": (
                    self._total_time[operation] / self._call_counts[operation]
                    if self._call_counts[operation] > 0 else 0
                ),
            }
        else:
            return {
                op: self.get_stats(op)
                for op in self._call_counts.keys()
            }

    def reset(self, operation: Optional[str] = None):
        """重置统计"""
        if operation:
            self._call_counts.pop(operation, None)
            self._retry_counts.pop(operation, None)
            self._success_counts.pop(operation, None)
            self._failure_counts.pop(operation, None)
            self._total_time.pop(operation, None)
        else:
            self._call_counts.clear()
            self._retry_counts.clear()
            self._success_counts.clear()
            self._failure_counts.clear()
            self._total_time.clear()


# 全局跟踪器实例
_tracker = LLMRetryTracker()


def get_tracker() -> LLMRetryTracker:
    """获取全局重试跟踪器"""
    return _tracker


__all__ = [
    "with_llm_retry",
    "with_async_llm_retry",
    "LLMTimeoutError",
    "LLMRateLimitError",
    "LLMConnectionError",
    "LLMInvalidResponseError",
    "is_retryable_error",
    "LLMRetryTracker",
    "get_tracker",
]
