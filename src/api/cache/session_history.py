"""
会话历史管理模块

提供统一的会话历史缓存管理，被 chat.py 和 chat_stream.py 共享使用
"""

from typing import Dict, List, Any
import time
from ...story.llm import Message, MessageRole


class SessionHistoryManager:
    """
    会话历史管理器

    管理多个会话的历史消息，支持时间戳跟踪和历史长度限制
    """

    def __init__(self, max_history: int = 50):
        """
        初始化会话历史管理器

        Args:
            max_history: 每个会话保留的最大历史消息数
        """
        self._history: Dict[str, List[Message]] = {}
        self._timestamps: Dict[str, float] = {}
        self._max_history = max_history

    def get_history(self, session_id: str) -> List[Message]:
        """
        获取会话历史

        Args:
            session_id: 会话ID

        Returns:
            该会话的历史消息列表
        """
        return self._history.get(session_id, []).copy()

    def add_message(
        self,
        session_id: str,
        role: MessageRole,
        content: str
    ) -> None:
        """
        添加消息到会话历史

        Args:
            session_id: 会话ID
            role: 消息角色
            content: 消息内容
        """
        if session_id not in self._history:
            self._history[session_id] = []
            self._timestamps[session_id] = time.time()

        self._history[session_id].append(
            Message(role=role, content=content)
        )

        # 限制历史长度
        if len(self._history[session_id]) > self._max_history:
            self._history[session_id] = self._history[session_id][-self._max_history:]

        # 更新时间戳
        self._timestamps[session_id] = time.time()

    def clear_session(self, session_id: str) -> None:
        """
        清除指定会话的历史

        Args:
            session_id: 会话ID
        """
        self._history.pop(session_id, None)
        self._timestamps.pop(session_id, None)

    def clear_all(self) -> None:
        """清除所有会话历史"""
        self._history.clear()
        self._timestamps.clear()

    def get_timestamp(self, session_id: str) -> float:
        """
        获取会话的最后更新时间戳

        Args:
            session_id: 会话ID

        Returns:
            时间戳，如果会话不存在返回0
        """
        return self._timestamps.get(session_id, 0)

    def get_all_session_ids(self) -> List[str]:
        """
        获取所有活跃的会话ID

        Returns:
            会话ID列表
        """
        return list(self._history.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            包含统计信息的字典
        """
        return {
            "total_sessions": len(self._history),
            "session_ids": list(self._history.keys()),
            "max_history_per_session": self._max_history,
            "total_messages": sum(len(msgs) for msgs in self._history.values()),
        }


# 全局会话历史管理器实例
_global_manager: SessionHistoryManager = None


def get_session_history_manager() -> SessionHistoryManager:
    """
    获取全局会话历史管理器实例

    Returns:
        SessionHistoryManager 实例
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = SessionHistoryManager(max_history=50)
    return _global_manager


def reset_session_history_manager() -> None:
    """重置全局会话历史管理器"""
    global _global_manager
    _global_manager = None


__all__ = [
    "SessionHistoryManager",
    "get_session_history_manager",
    "reset_session_history_manager",
]
