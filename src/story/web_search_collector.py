"""
联网搜索收集器
Web Search Collector

通过联网搜索获取创作素材
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from .material_collector import (
    MaterialCollector,
    MaterialSource,
    MaterialCategory,
    Material,
    CollectionRequest,
    CollectionResult,
)


class WebSearchCollector(MaterialCollector):
    """联网搜索收集器

    支持多种搜索后端
    """

    def __init__(self, search_backend: str = "mock"):
        """
        Args:
            search_backend: 搜索后端类型 ("mock", "mcp")
        """
        self.search_backend = search_backend
        self._mcp_available = False

        # 尝试导入 MCP 搜索工具
        if search_backend == "mcp":
            try:
                # 这里将在运行时通过 MCP 工具调用
                self._mcp_available = True
            except ImportError:
                print("MCP search not available, falling back to mock")
                self.search_backend = "mock"

    def get_source_type(self) -> MaterialSource:
        return MaterialSource.WEB_SEARCH

    def collect(self, request: CollectionRequest) -> CollectionResult:
        """从联网搜索收集素材"""
        import time
        start_time = time.time()

        materials = []

        # 根据搜索后端选择实现
        if self.search_backend == "mcp" and self._mcp_available:
            materials = self._search_with_mcp(request)
        else:
            materials = self._search_mock(request)

        collection_time = time.time() - start_time

        return CollectionResult(
            materials=materials,
            total_count=len(materials),
            source_breakdown={MaterialSource.WEB_SEARCH.value: len(materials)},
            collection_time=collection_time,
        )

    def _search_with_mcp(self, request: CollectionRequest) -> List[Material]:
        """使用 MCP 工具进行搜索（占位实现）

        注意：实际使用时需要在外部调用 MCP 工具并传入结果
        此方法作为接口定义，实际搜索在 agent 层完成
        """
        # 此方法不会被直接调用，而是通过外部传入搜索结果
        # 参考 _set_search_results 方法
        return []

    def _search_mock(self, request: CollectionRequest) -> List[Material]:
        """Mock 搜索实现（用于开发测试）"""
        # 模拟搜索结果
        mock_results = self._generate_mock_results(request)

        materials = []
        for result in mock_results:
            material = Material(
                content=result["content"],
                source=MaterialSource.WEB_SEARCH,
                category=request.category or MaterialCategory.KNOWLEDGE,
                credibility_score=0.5,  # 默认可信度
                relevance_score=result.get("relevance", 0.6),
                metadata={
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "has_reference": True,
                },
                tags=set(result.get("tags", [])),
            )
            materials.append(material)

        return materials[:request.max_results]

    def _generate_mock_results(self, request: CollectionRequest) -> List[Dict[str, Any]]:
        """生成模拟搜索结果"""
        # 根据查询关键词生成相关内容
        query_lower = request.query.lower()

        # 模拟搜索结果数据库
        mock_database = {
            "武侠": [
                {
                    "content": "武侠小说是中国传统文学的重要形式，强调侠义精神和武学修养。",
                    "title": "武侠小说概述",
                    "url": "https://example.com/wuxia-overview",
                    "tags": ["武侠", "文学", "传统"],
                },
                {
                    "content": "武功修炼通常分为内功和外功，内功修炼气息，外功修炼招式。",
                    "title": "武功修炼体系",
                    "url": "https://example.com/martial-arts",
                    "tags": ["武功", "修炼", "体系"],
                },
            ],
            "仙侠": [
                {
                    "content": "仙侠小说融合了道教文化和武侠元素，主角追求长生不老。",
                    "title": "仙侠小说特点",
                    "url": "https://example.com/xianxia",
                    "tags": ["仙侠", "道教", "长生"],
                },
                {
                    "content": "修仙境界通常分为：炼气、筑基、金丹、元婴、化神等。",
                    "title": "修仙境界体系",
                    "url": "https://example.com/cultivation-levels",
                    "tags": ["修仙", "境界", "体系"],
                },
            ],
            "科幻": [
                {
                    "content": "科幻小说探索科技发展对人类社会的影响和未来可能性。",
                    "title": "科幻小说概述",
                    "url": "https://example.com/sci-fi",
                    "tags": ["科幻", "科技", "未来"],
                },
                {
                    "content": "人工智能、基因工程、太空探索是常见科幻主题。",
                    "title": "常见科幻主题",
                    "url": "https://example.com/sci-fi-themes",
                    "tags": ["AI", "基因工程", "太空"],
                },
            ],
        }

        results = []

        # 根据查询匹配模拟结果
        for keyword, items in mock_database.items():
            if keyword in query_lower:
                for item in items:
                    results.append({
                        **item,
                        "relevance": 0.7,
                    })

        # 如果没有匹配，返回通用结果
        if not results:
            results.append({
                "content": f"关于'{request.query}'的相关知识和背景信息。",
                "title": f"搜索结果: {request.query}",
                "url": "https://example.com/search",
                "tags": ["通用"],
                "relevance": 0.5,
            })

        return results

    def set_search_results(
        self,
        request: CollectionRequest,
        search_results: List[Dict[str, Any]],
    ) -> CollectionResult:
        """设置外部搜索结果并转换为素材

        用于接收从 MCP 工具或其他外部搜索获得的结果

        Args:
            request: 收集请求
            search_results: 搜索结果列表，每个结果包含:
                - title: 标题
                - url: 链接
                - snippet/summary: 摘要
                - content: 完整内容（可选）
        """
        import time
        start_time = time.time()

        materials = []
        for result in search_results:
            # 优先使用 content，其次使用 snippet
            content = result.get(
                "content",
                result.get("summary", result.get("snippet", "")),
            )

            if not content:
                continue

            material = Material(
                content=content,
                source=MaterialSource.WEB_SEARCH,
                category=request.category or self._infer_category(result),
                credibility_score=0.5,  # 网络搜索基础可信度
                relevance_score=result.get("relevance", 0.6),
                metadata={
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "has_reference": bool(result.get("url", "")),
                    "source_domain": self._extract_domain(result.get("url", "")),
                },
                tags=set(result.get("tags", [])),
            )
            materials.append(material)

        collection_time = time.time() - start_time

        return CollectionResult(
            materials=materials[:request.max_results],
            total_count=len(materials[:request.max_results]),
            source_breakdown={MaterialSource.WEB_SEARCH.value: len(materials[:request.max_results])},
            collection_time=collection_time,
        )

    def _infer_category(self, result: Dict[str, Any]) -> MaterialCategory:
        """根据搜索结果推断素材分类"""
        title = result.get("title", "").lower()
        content = result.get("content", "").lower()
        text = f"{title}{content}"

        # 简单的关键词匹配
        if any(keyword in text for keyword in ["人物", "角色", "主角", "性格"]):
            return MaterialCategory.CHARACTER
        elif any(keyword in text for keyword in ["世界", "设定", "背景", "体系"]):
            return MaterialCategory.SETTING
        elif any(keyword in text for keyword in ["情节", "事件", "故事", "冲突"]):
            return MaterialCategory.PLOT
        else:
            return MaterialCategory.KNOWLEDGE

    def _extract_domain(self, url: str) -> str:
        """从 URL 提取域名"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""


class MockWebSearchCollector(WebSearchCollector):
    """Mock 网络搜索收集器（用于测试）"""

    def __init__(self):
        super().__init__(search_backend="mock")

    def _search_mock(self, request: CollectionRequest) -> List[Material]:
        """生成更丰富的模拟结果"""
        # 内置的模拟知识库
        knowledge_base = {
            "剑法": [
                "独孤九剑：重在破招，无招胜有招",
                "太极剑法：以柔克刚，四两拨千斤",
                "辟邪剑法：速度快，招式诡异",
            ],
            "内功": [
                "九阳神功：至阳至刚，护体神功",
                "九阴真经：阴阳调和，刚柔并济",
                "易筋经：佛门内功，化腐朽为神奇",
            ],
            "轻功": [
                "梯云纵：武当派轻功，可凌空虚度",
                "凌波微步：逍遥派轻功，步法精妙",
            ],
            "兵器": [
                "玄铁重剑：重剑无锋，大巧不工",
                "倚天剑：锋利无比，斩金断玉",
                "金箍棒：如意金箍棒，大小随心",
            ],
        }

        materials = []
        query_lower = request.query.lower()

        # 匹配查询
        for keyword, contents in knowledge_base.items():
            if keyword in query_lower:
                for i, content in enumerate(contents):
                    material = Material(
                        content=content,
                        source=MaterialSource.WEB_SEARCH,
                        category=request.category or MaterialCategory.KNOWLEDGE,
                        credibility_score=0.5,
                        relevance_score=0.8 - i * 0.1,  # 递减的相关性
                        metadata={
                            "title": f"{keyword}相关资料",
                            "url": f"https://example.com/{keyword}",
                            "has_reference": True,
                        },
                        tags={keyword, "武侠"},
                    )
                    materials.append(material)

        # 如果没有匹配，返回通用结果
        if not materials:
            material = Material(
                content=f"关于'{request.query}'的搜索结果：这是一个常见的创作主题。",
                source=MaterialSource.WEB_SEARCH,
                category=request.category or MaterialCategory.KNOWLEDGE,
                credibility_score=0.5,
                relevance_score=0.5,
                metadata={
                    "title": f"搜索: {request.query}",
                    "url": "https://example.com/search",
                },
            )
            materials.append(material)

        return materials[:request.max_results]
