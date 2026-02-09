"""
用户分析 API

用于跟踪和分析用户行为（隐私优先设计）
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["分析"])

# ============================================================
# 请求/响应模型
# ============================================================

class AnalyticsEvent(BaseModel):
    """分析事件"""
    event_type: str  # 事件类型: page_view, feature_use, etc.
    event_name: str  # 事件名称
    properties: Dict[str, Any] = {}  # 事件属性
    timestamp: datetime = None  # 时间戳（可选，默认当前时间）


class AnalyticsStats(BaseModel):
    """统计信息"""
    total_events: int
    unique_users: int
    events_by_type: Dict[str, int]
    top_features: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime


# ============================================================
# 内存存储（生产环境应使用数据库）
# ============================================================

# 简化版本：使用内存存储
# 生产环境应该使用 PostgreSQL 或其他数据库
_events_storage: List[Dict[str, Any]] = []
_max_events = 10000  # 最多存储多少事件


def _trim_events():
    """保持事件存储在限制内"""
    global _events_storage
    if len(_events_storage) > _max_events:
        # 保留最近的事件
        _events_storage = _events_storage[-_max_events:]


def _get_user_id(request) -> str:
    """获取用户 ID（匿名）"""
    # 从请求头或认证信息中获取用户 ID
    # 如果没有，返回匿名 ID
    headers = request.headers
    user_id = headers.get("X-User-ID")
    if user_id:
        return user_id

    # 尝试从认证中获取
    auth_header = headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # 简化处理：使用 token 的一部分作为用户 ID
        import hashlib
        token = auth_header[7:]
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    # 完全匿名
    return "anonymous"


# ============================================================
# API 端点
# ============================================================

@router.post("/track")
async def track_event(event: AnalyticsEvent, request) -> Dict[str, str]:
    """
    记录分析事件

    - **event_type**: 事件类型（page_view, feature_use, error, etc.）
    - **event_name**: 事件名称
    - **properties**: 事件属性（可选）
    """
    # 设置时间戳
    if event.timestamp is None:
        event.timestamp = datetime.utcnow()

    # 获取用户 ID（匿名）
    user_id = _get_user_id(request)

    # 存储事件
    event_data = {
        "event_type": event.event_type,
        "event_name": event.event_name,
        "properties": event.properties,
        "timestamp": event.timestamp.isoformat(),
        "user_id": user_id,
        # 不记录敏感信息（IP、具体内容等）
    }

    _events_storage.append(event_data)
    _trim_events()

    logger.debug(f"Analytics event recorded: {event.event_type} - {event.event_name}")

    return {"status": "recorded", "event_id": str(len(_events_storage))}


@router.get("/stats")
async def get_stats(
    days: int = 7,
    request = None
) -> AnalyticsStats:
    """
    获取统计信息

    - **days**: 统计最近多少天的数据（默认 7 天）
    """
    # 计算时间范围
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    # 过滤事件
    filtered_events = [
        e for e in _events_storage
        if datetime.fromisoformat(e["timestamp"]) >= start_time
    ]

    # 计算统计
    total_events = len(filtered_events)
    unique_users = len(set(e["user_id"] for e in filtered_events))

    # 按事件类型分组
    events_by_type: Dict[str, int] = {}
    for event in filtered_events:
        event_type = event["event_type"]
        events_by_type[event_type] = events_by_type.get(event_type, 0) + 1

    # 热门功能
    feature_events = [e for e in filtered_events if e["event_type"] == "feature_use"]
    feature_counts: Dict[str, int] = {}
    for event in feature_events:
        feature_name = event["properties"].get("feature", "unknown")
        feature_counts[feature_name] = feature_counts.get(feature_name, 0) + 1

    top_features = [
        {"feature": name, "count": count}
        for name, count in sorted(feature_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return AnalyticsStats(
        total_events=total_events,
        unique_users=unique_users,
        events_by_type=events_by_type,
        top_features=top_features,
        period_start=start_time,
        period_end=end_time,
    )


@router.post("/consent")
async def update_consent(consent: bool) -> Dict[str, Any]:
    """
    更新用户分析同意状态

    前端应调用此端点记录用户是否同意数据分析
    """
    # 在实际实现中，这应该存储在数据库中
    # 并与用户 ID 关联

    return {
        "status": "updated",
        "analytics_consent": consent,
        "message": "分析同意状态已更新" if consent else "分析已禁用"
    }


@router.get("/consent")
async def get_consent() -> Dict[str, Any]:
    """
    获取当前分析同意状态
    """
    # 在实际实现中，这应该从数据库中读取
    return {
        "analytics_enabled": True,
        "data_retention_days": 30,
        "anonymous_only": True,  # 仅收集匿名数据
    }


__all__ = ["router"]
