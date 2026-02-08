"""
LRU 会话历史缓存

使用 OrderedDict 实现真正的 LRU 缓存，解决内存泄漏风险
支持：
- 最大缓存条目数限制
- TTL 过期自动清理
- 每个会话最大历史消息数限制
- 线程安全
"""

import threading
import time
import logging
from collections import OrderedDict
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from ...story.llm import Message, MessageRole

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """缓存条目"""
    messages: List[Message]
    timestamp: float
    access_count: int = 0


class LRUSessionCache:
    """
    LRU 会话历史缓存

    特性：
    - 使用 OrderedDict 实现 O(1) 的 get/set 操作
    - 访问时自动移动到末尾（最近使用）
    - 达到上限时自动淘汰最久未使用的会话
    - 定期清理过期条目
    - 线程安全（使用 RLock）
    """

    def __init__(
        self,
        maxsize: int = 100,
        ttl: int = 3600,
        max_history: int = 20
    ):
        """
        初始化 LRU 缓存

        Args:
            maxsize: 最大缓存会话数
            ttl: 会话TTL（秒），默认1小时
            max_history: 每个会话最大历史消息数
        """
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.RLock()
        self._maxsize = maxsize
        self._ttl = ttl
        self._max_history = max_history

        # 统计信息
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0,
        }

    def _is_expired(self, entry: CacheEntry) -> bool:
        """检查条目是否过期"""
        return time.time() - entry.timestamp > self._ttl

    def _cleanup_expired(self) -> int:
        """清理过期的条目，返回清理数量"""
        expired_keys = []
        current_time = time.time()

        for key, entry in self._cache.items():
            if current_time - entry.timestamp > self._ttl:
                expired_keys.append(key)
            else:
                # OrderedDict 按插入顺序排列，遇到未过期的就可以停止
                break

        for key in expired_keys:
            del self._cache[key]
            self._stats["expirations"] += 1

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired session(s)")

        return len(expired_keys)

    def _evict_lru(self) -> None:
        """淘汰最久未使用的条目"""
        if not self._cache:
            return

        # 弹出第一个（最久未使用）
        key, _ = self._cache.popitem(last=False)
        self._stats["evictions"] += 1
        logger.debug(f"Evicted LRU session: {key}")

    def _enforce_maxsize(self) -> None:
        """强制执行最大条目数限制"""
        # 先清理过期条目
        self._cleanup_expired()

        # 如果还是超过限制，淘汰最久未使用的
        while len(self._cache) >= self._maxsize:
            self._evict_lru()

    def get(self, session_id: str) -> List[Message]:
        """
        获取会话历史

        访问时会将条目移动到末尾（标记为最近使用）
        """
        with self._lock:
            # 定期清理（每次访问都检查）
            self._cleanup_expired()

            entry = self._cache.get(session_id)

            if entry is None:
                self._stats["misses"] += 1
                return []

            # 检查是否过期
            if self._is_expired(entry):
                del self._cache[session_id]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return []

            # 移动到末尾（标记为最近使用）
            self._cache.move_to_end(session_id)
            entry.access_count += 1
            entry.timestamp = time.time()  # 更新访问时间

            self._stats["hits"] += 1
            return entry.messages.copy()

    def set(self, session_id: str, messages: List[Message]) -> None:
        """
        设置会话历史

        会将条目添加到末尾（标记为最近使用）
        """
        with self._lock:
            # 强制执行大小限制
            self._enforce_maxsize()

            # 限制历史长度
            if len(messages) > self._max_history:
                messages = messages[-self._max_history:]

            entry = CacheEntry(
                messages=messages.copy(),
                timestamp=time.time(),
                access_count=0
            )

            # 如果已存在，先删除再添加（确保移动到末尾）
            if session_id in self._cache:
                del self._cache[session_id]

            self._cache[session_id] = entry

    def add_message(self, session_id: str, role: MessageRole, content: str) -> None:
        """
        向会话添加单条消息

        这是最常用的操作，优化性能
        """
        with self._lock:
            entry = self._cache.get(session_id)

            if entry is None or self._is_expired(entry):
                # 创建新条目
                messages = [Message(role=role, content=content)]
                self.set(session_id, messages)
                return

            # 添加消息并限制长度
            entry.messages.append(Message(role=role, content=content))
            if len(entry.messages) > self._max_history:
                entry.messages = entry.messages[-self._max_history:]

            # 更新时间和访问计数
            entry.timestamp = time.time()
            entry.access_count += 1

            # 移动到末尾
            self._cache.move_to_end(session_id)

    def delete(self, session_id: str) -> bool:
        """删除会话历史"""
        with self._lock:
            if session_id in self._cache:
                del self._cache[session_id]
                logger.debug(f"Deleted session: {session_id}")
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"Cleared all {count} cached session(s)")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0

            return {
                "size": len(self._cache),
                "maxsize": self._maxsize,
                "ttl": self._ttl,
                "max_history": self._max_history,
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "hit_rate": hit_rate,
                "evictions": self._stats["evictions"],
                "expirations": self._stats["expirations"],
                "sessions": list(self._cache.keys()),
            }

    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取特定会话的详细信息"""
        with self._lock:
            entry = self._cache.get(session_id)
            if entry is None:
                return None

            age = time.time() - entry.timestamp
            return {
                "session_id": session_id,
                "message_count": len(entry.messages),
                "age_seconds": age,
                "access_count": entry.access_count,
                "is_expired": age > self._ttl,
            }


# 全局单例
_global_cache: Optional[LRUSessionCache] = None


def get_session_cache() -> LRUSessionCache:
    """获取全局会话缓存实例（单例）"""
    global _global_cache
    if _global_cache is None:
        _global_cache = LRUSessionCache(
            maxsize=100,  # 最多缓存100个会话
            ttl=3600,     # 1小时过期
            max_history=20  # 每个会话最多20条消息
        )
    return _global_cache


def reset_session_cache() -> None:
    """重置全局会话缓存"""
    global _global_cache
    _global_cache = None


__all__ = [
    "LRUSessionCache",
    "get_session_cache",
    "reset_session_cache",
]
