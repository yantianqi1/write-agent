"""
性能监控中间件

提供内存、CPU、并发连接等系统指标监控
"""

import time
import threading
import logging
import psutil
from typing import Dict, Any, Optional
from collections import deque
from functools import wraps
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    性能指标收集器

    收集以下指标：
    - 请求计数（按状态码、路径）
    - 响应时间（最小、最大、平均、P95、P99）
    - 并发连接数
    - 系统资源使用（CPU、内存）
    """

    def __init__(self, max_samples: int = 1000):
        self._lock = threading.RLock()

        # 请求统计
        self._request_count: Dict[str, int] = {}
        self._request_times: deque = deque(maxlen=max_samples)
        self._request_errors: deque = deque(maxlen=100)

        # 并发统计
        self._active_requests: int = 0
        self._max_active_requests: int = 0
        self._total_requests: int = 0

        # 系统资源采样
        self._cpu_samples: deque = deque(maxlen=60)  # 最近60秒
        self._memory_samples: deque = deque(maxlen=60)

        # 启动时间
        self._start_time = time.time()

    def record_request(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        error: Optional[str] = None
    ) -> None:
        """记录请求指标"""
        with self._lock:
            key = f"{method} {path}"
            self._request_count[key] = self._request_count.get(key, 0) + 1
            self._request_times.append({
                'key': key,
                'status': status_code,
                'duration': duration,
                'timestamp': time.time(),
            })

            if error:
                self._request_errors.append({
                    'key': key,
                    'error': error,
                    'timestamp': time.time(),
                })

    def record_active_request(self, delta: int) -> None:
        """更新活跃请求数"""
        with self._lock:
            self._active_requests += delta
            if delta > 0:
                self._total_requests += 1
                if self._active_requests > self._max_active_requests:
                    self._max_active_requests = self._active_requests

    def sample_system_resources(self) -> None:
        """采样系统资源使用情况"""
        with self._lock:
            try:
                process = psutil.Process()
                self._cpu_samples.append(process.cpu_percent())
                memory_info = process.memory_info()
                self._memory_samples.append({
                    'rss': memory_info.rss,  # 常驻内存
                    'vms': memory_info.vms,  # 虚拟内存
                    'percent': process.memory_percent(),
                })
            except Exception as e:
                logger.warning(f"Failed to sample system resources: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """获取当前指标"""
        with self._lock:
            # 计算响应时间统计
            durations = [r['duration'] for r in self._request_times]
            response_time_stats = {}
            if durations:
                sorted_durations = sorted(durations)
                response_time_stats = {
                    'min': round(min(durations), 3),
                    'max': round(max(durations), 3),
                    'avg': round(sum(durations) / len(durations), 3),
                    'p95': round(sorted_durations[int(len(sorted_durations) * 0.95)], 3),
                    'p99': round(sorted_durations[int(len(sorted_durations) * 0.99)], 3),
                }

            # 计算系统资源统计
            cpu_stats = {}
            if self._cpu_samples:
                cpu_samples_list = list(self._cpu_samples)
                cpu_stats = {
                    'current': round(cpu_samples_list[-1], 2),
                    'avg': round(sum(cpu_samples_list) / len(cpu_samples_list), 2),
                    'max': round(max(cpu_samples_list), 2),
                }

            memory_stats = {}
            if self._memory_samples:
                latest_mem = self._memory_samples[-1]
                memory_stats = {
                    'rss_mb': round(latest_mem['rss'] / 1024 / 1024, 2),
                    'vms_mb': round(latest_mem['vms'] / 1024 / 1024, 2),
                    'percent': round(latest_mem['percent'], 2),
                }

            # 计算状态码分布
            status_counts: Dict[int, int] = {}
            for r in self._request_times:
                status = r['status']
                status_counts[status] = status_counts.get(status, 0) + 1

            uptime = time.time() - self._start_time

            return {
                'uptime_seconds': round(uptime, 2),
                'requests': {
                    'total': self._total_requests,
                    'active': self._active_requests,
                    'max_active': self._max_active_requests,
                    'by_endpoint': dict(self._request_count),
                    'by_status': status_counts,
                },
                'response_time': response_time_stats,
                'system': {
                    'cpu': cpu_stats,
                    'memory': memory_stats,
                },
                'recent_errors': list(self._request_errors)[-10:],
            }

    def reset(self) -> None:
        """重置所有指标"""
        with self._lock:
            self._request_count.clear()
            self._request_times.clear()
            self._request_errors.clear()
            self._active_requests = 0
            self._max_active_requests = 0
            self._total_requests = 0
            self._cpu_samples.clear()
            self._memory_samples.clear()
            self._start_time = time.time()


# 全局指标实例
_metrics: Optional[PerformanceMetrics] = None


def get_metrics() -> PerformanceMetrics:
    """获取全局指标实例"""
    global _metrics
    if _metrics is None:
        _metrics = PerformanceMetrics()
    return _metrics


def reset_metrics() -> None:
    """重置全局指标"""
    global _metrics
    _metrics = None


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    监控中间件

    自动记录每个请求的性能指标
    """

    def __init__(self, app: ASGIApp, metrics: Optional[PerformanceMetrics] = None):
        super().__init__(app)
        self._metrics = metrics or get_metrics()

    async def dispatch(self, request: Request, call_next):
        """处理请求并记录指标"""
        metrics = self._metrics
        metrics.record_active_request(1)

        # 记录开始时间
        start_time = time.time()

        # 处理请求
        error = None
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            error = str(e)
            status_code = 500
            # 创建错误响应
            response = Response(
                content=f"Internal Server Error: {error}",
                status_code=500
            )
        finally:
            # 记录指标
            duration = time.time() - start_time
            method = request.method
            path = request.url.path

            # 跳过健康检查端点的详细记录
            if path != '/health':
                metrics.record_request(
                    method=method,
                    path=path,
                    status_code=status_code,
                    duration=duration,
                    error=error
                )

            metrics.record_active_request(-1)

        return response


def start_background_sampler(interval: int = 1) -> threading.Thread:
    """
    启动后台采样线程

    Args:
        interval: 采样间隔（秒）

    Returns:
        采样线程
    """
    def sampler():
        while True:
            time.sleep(interval)
            get_metrics().sample_system_resources()

    thread = threading.Thread(target=sampler, daemon=True)
    thread.start()
    logger.info(f"Started background resource sampler with {interval}s interval")
    return thread


__all__ = [
    "PerformanceMetrics",
    "MonitoringMiddleware",
    "get_metrics",
    "reset_metrics",
    "start_background_sampler",
]
