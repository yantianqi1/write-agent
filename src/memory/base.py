"""
记忆系统基础接口
Base Memory Interface

定义记忆存储的抽象接口和记忆层级枚举
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class MemoryLevel(Enum):
    """记忆层级枚举"""
    GLOBAL = "global"           # 全局记忆：世界观设定、核心主题、整体大纲
    CHARACTER = "character"      # 角色记忆：人物档案、性格特征、关系图谱
    PLOT = "plot"                # 情节记忆：已发生事件、伏笔列表、未解决冲突
    CONTEXT = "context"          # 近期上下文：最近2-3章的详细内容
    STYLE = "style"              # 风格记忆：叙事风格、常用表达、节奏模式


class MemoryItem:
    """记忆项数据结构"""

    def __init__(
        self,
        level: MemoryLevel,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
    ):
        self.level = level
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()
        self.id = f"{level.value}_{self.timestamp.timestamp()}"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "level": self.level.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
        }


class MemoryStore(ABC):
    """记忆存储抽象基类"""

    @abstractmethod
    def add(self, item: MemoryItem) -> str:
        """添加记忆项，返回记忆 ID"""
        pass

    @abstractmethod
    def get(self, memory_id: str) -> Optional[MemoryItem]:
        """根据 ID 获取记忆项"""
        pass

    @abstractmethod
    def update(self, memory_id: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """更新记忆项"""
        pass

    @abstractmethod
    def delete(self, memory_id: str):
        """删除记忆项"""
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        level: Optional[MemoryLevel] = None,
        limit: int = 10,
    ) -> List[MemoryItem]:
        """根据查询搜索记忆项"""
        pass

    @abstractmethod
    def get_by_level(self, level: MemoryLevel, limit: int = 100) -> List[MemoryItem]:
        """根据层级获取记忆项"""
        pass
