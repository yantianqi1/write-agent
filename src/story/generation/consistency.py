"""
Consistency checking and enforcement module.

This module provides mechanisms to ensure consistency across
generated content including character behavior, world rules,
and plot logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re

from ..setting_extractor.models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement
)


class ConsistencyLevel(Enum):
    """Level of consistency issue."""
    INFO = "info"  # Minor note
    WARNING = "warning"  # Potential inconsistency
    ERROR = "error"  # Clear inconsistency that should be fixed
    CRITICAL = "critical"  # Breaking inconsistency


@dataclass
class ConsistencyIssue:
    """A consistency issue found in content."""
    level: ConsistencyLevel
    category: str  # "character", "world", "plot", "style"
    description: str
    location: str = ""  # Where in the content
    suggestion: str = ""
    affected_elements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level.value,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "suggestion": self.suggestion,
            "affected_elements": self.affected_elements.copy()
        }


@dataclass
class ConsistencyReport:
    """Report of consistency check."""
    issues: List[ConsistencyIssue] = field(default_factory=list)
    score: float = 1.0  # 0.0 to 1.0, higher is more consistent
    passed: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_issue(self, issue: ConsistencyIssue) -> None:
        """Add an issue to the report."""
        self.issues.append(issue)
        if issue.level in (ConsistencyLevel.ERROR, ConsistencyLevel.CRITICAL):
            self.passed = False

    def calculate_score(self) -> None:
        """Calculate consistency score."""
        if not self.issues:
            self.score = 1.0
            return

        # Weight issues by severity
        weights = {
            ConsistencyLevel.INFO: 0.0,
            ConsistencyLevel.WARNING: 0.1,
            ConsistencyLevel.ERROR: 0.3,
            ConsistencyLevel.CRITICAL: 0.5
        }

        total_penalty = sum(weights.get(issue.level, 0) for issue in self.issues)
        self.score = max(0.0, 1.0 - total_penalty)

    def get_critical_issues(self) -> List[ConsistencyIssue]:
        """Get all critical issues."""
        return [i for i in self.issues if i.level == ConsistencyLevel.CRITICAL]

    def get_warnings(self) -> List[ConsistencyIssue]:
        """Get all warnings and errors."""
        return [i for i in self.issues if i.level in (ConsistencyLevel.WARNING, ConsistencyLevel.ERROR)]


class CharacterTracker:
    """
    Tracks character state throughout the story.

    Monitors:
    - Current location
    - Current state (alive, injured, etc.)
    - Knowledge and memories
    - Relationships
    - Inventory/possessions
    """

    def __init__(self, characters: List[CharacterProfile]):
        """Initialize with character profiles."""
        self.character_states: Dict[str, Dict[str, Any]] = {}
        for char in characters:
            name = char.name or "未命名角色"
            self.character_states[name] = {
                "profile": char,
                "last_location": "未知",
                "status": "正常",
                "knowledge": set(),
                "relationships": dict(char.relationships) if char.relationships else {},
                "last_appearance_chapter": 0,
            }

    def update_from_content(self, content: str, chapter_number: int) -> List[ConsistencyIssue]:
        """
        Update character states from content and check for consistency.

        Args:
            content: Generated content
            chapter_number: Current chapter number

        Returns:
            List of consistency issues found
        """
        issues = []

        for name, state in self.character_states.items():
            # Check if character appears in content
            if name in content:
                state["last_appearance_chapter"] = chapter_number

                # Extract location mentions
                location_patterns = [
                    r"(?:在|来到|位于|走进)([^，。]{2,10?})(?:房间|地方|处)",
                    r"([^，。]{2,15?})(?:城中|城里|城外|村|镇|山|河|海)",
                ]

                for pattern in location_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        state["last_location"] = match.group(1)

                # Check for status changes
                if "受伤" in content and name in content:
                    state["status"] = "受伤"
                elif "死亡" in content or "牺牲" in content:
                    if name in content:
                        state["status"] = "死亡"

                # Check for character behavior consistency
                issues.extend(self._check_behavior_consistency(name, state, content))

        return issues

    def _check_behavior_consistency(self,
                                   name: str,
                                   state: Dict[str, Any],
                                   content: str) -> List[ConsistencyIssue]:
        """Check if character behavior matches their profile."""
        issues = []
        profile = state["profile"]

        # Skip if no personality defined
        if not profile or not profile.personality:
            return issues

        personality = profile.personality

        # Check for contradictory behavior
        if "勇敢" in personality and "胆怯" in content and name in content:
            # Find the specific context
            context_start = max(0, content.find(name) - 50)
            context_end = min(len(content), content.find(name) + 100)
            context = content[context_start:context_end]

            if "犹豫" in context or "退缩" in context:
                issues.append(ConsistencyIssue(
                    level=ConsistencyLevel.WARNING,
                    category="character",
                    description=f"{name}的行为与'勇敢'性格设定不符",
                    location=context[:50],
                    suggestion="除非有特殊原因，否则应保持勇敢的性格",
                    affected_elements=[name]
                ))

        if "冷静" in personality and ("冲动" in content or "愤怒" in content):
            if name in content:
                issues.append(ConsistencyIssue(
                    level=ConsistencyLevel.WARNING,
                    category="character",
                    description=f"{name}表现出与'冷静'性格不符的行为",
                    suggestion="考虑添加导致情绪失控的原因",
                    affected_elements=[name]
                ))

        return issues

    def get_character_state(self, name: str) -> Optional[Dict[str, Any]]:
        """Get current state of a character."""
        return self.character_states.get(name)

    def is_alive(self, name: str) -> bool:
        """Check if a character is alive."""
        state = self.character_states.get(name)
        return state and state["status"] != "死亡"


class WorldRuleChecker:
    """
    Checks consistency against world rules.

    Monitors:
    - Magic system rules
    - Technology level consistency
    - Geographic consistency
    - Timeline consistency
    """

    def __init__(self, world_setting: WorldSetting):
        """Initialize with world settings."""
        self.world = world_setting
        self.established_facts: Set[str] = set()
        self.locations: Set[str] = set()

    def check_content(self, content: str, chapter_number: int) -> List[ConsistencyIssue]:
        """Check content against world rules."""
        issues = []

        if not self.world:
            return issues

        # Check magic system consistency
        issues.extend(self._check_magic_consistency(content))

        # Check technology consistency
        issues.extend(self._check_technology_consistency(content))

        # Track locations
        self._track_locations(content)

        return issues

    def _check_magic_consistency(self, content: str) -> List[ConsistencyIssue]:
        """Check magic system consistency."""
        issues = []

        if not self.world or not self.world.magic_system:
            return issues

        # If world has magic, check for mentions
        has_magic = self.world.magic_system != "无魔法"
        content_has_magic = (
            "魔法" in content or "法术" in content or "咒语" in content or
            "magic" in content.lower() or "spell" in content.lower()
        )

        if has_magic and not content_has_magic:
            # This is okay - not every scene needs magic
            pass
        elif not has_magic and content_has_magic:
            issues.append(ConsistencyIssue(
                level=ConsistencyLevel.ERROR,
                category="world",
                description="内容包含魔法元素，但世界观设定为无魔法",
                suggestion="检查世界观设定或移除魔法相关描述",
                affected_elements=["world_setting"]
            ))

        return issues

    def _check_technology_consistency(self, content: str) -> List[ConsistencyIssue]:
        """Check technology level consistency."""
        issues = []

        if not self.world or not self.world.technology_level:
            return issues

        # Check for anachronisms
        tech_keywords = {
            "中世纪": ["枪", "炮", "电脑", "手机", "汽车", "飞机"],
            "古代": ["电灯", "电话", "枪炮", "现代"],
            "科幻": ["马车", "剑术", "冷兵器"],  # Unless specifically retro
        }

        for era, keywords in tech_keywords.items():
            if era in self.world.technology_level:
                for keyword in keywords:
                    if keyword in content:
                        issues.append(ConsistencyIssue(
                            level=ConsistencyLevel.WARNING,
                            category="world",
                            description=f"内容包含可能与'{self.world.technology_level}'不符的元素：{keyword}",
                            suggestion="确认这是有意为之或修改设定",
                            affected_elements=["technology_level"]
                        ))

        return issues

    def _track_locations(self, content: str) -> None:
        """Extract and track locations mentioned in content."""
        # Simple location extraction patterns
        patterns = [
            r"(?:来到|位于|在)([^，。]{2,15?})(?:城|镇|村|山|河|海|宫殿|城堡)",
            r"([^，。]{2,15?})(?:的街道|的广场|的森林|的边缘)",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                self.locations.add(match.group(1))


class PlotConsistencyChecker:
    """
    Checks plot consistency across chapters.

    Monitors:
    - Event sequence consistency
    - Causal relationships
    - Character knowledge and motivations
    - Timeline consistency
    """

    def __init__(self, plot: PlotElement):
        """Initialize with plot elements."""
        self.plot = plot
        self.events: List[Dict[str, Any]] = []
        self.timeline: List[str] = []

    def check_content(self,
                     content: str,
                     chapter_number: int,
                     previous_content: str = "") -> List[ConsistencyIssue]:
        """Check plot consistency."""
        issues = []

        # Track events
        self._track_events(content, chapter_number)

        # Check for contradictions with previous content
        if previous_content:
            issues.extend(self._check_contradictions(content, previous_content))

        # Check plot progression
        issues.extend(self._check_plot_progression(content, chapter_number))

        return issues

    def _track_events(self, content: str, chapter_number: int) -> None:
        """Extract and track events from content."""
        # Simple event extraction - look for action sentences
        sentences = re.split(r'[。！？]', content)
        for sentence in sentences:
            if any(kw in sentence for kw in ["突然", "接着", "然后", "于是", "之后"]):
                self.events.append({
                    "chapter": chapter_number,
                    "description": sentence.strip(),
                    "type": self._classify_event(sentence)
                })

    def _classify_event(self, sentence: str) -> str:
        """Classify event type."""
        if any(kw in sentence for kw in ["战斗", "打斗", "攻击"]):
            return "combat"
        elif any(kw in sentence for kw in ["发现", "意识到", "明白"]):
            return "discovery"
        elif any(kw in sentence for kw in ["决定", "下定决心"]):
            return "decision"
        elif any(kw in sentence for kw in ["死亡", "牺牲", "受伤"]):
            return "consequence"
        return "action"

    def _check_contradictions(self,
                             content: str,
                             previous_content: str) -> List[ConsistencyIssue]:
        """Check for contradictions with previous content."""
        issues = []

        # Simple contradiction checks
        # Check status reversals
        status_pairs = [
            ("活着", "死亡"),
            ("在一起", "分开"),
            ("知道", "不知道"),
        ]

        for positive, negative in status_pairs:
            if positive in previous_content and negative in content:
                issues.append(ConsistencyIssue(
                    level=ConsistencyLevel.ERROR,
                    category="plot",
                    description=f"可能的状态矛盾：前文提到'{positive}'，当前内容提到'{negative}'",
                    suggestion="确保角色状态变化的逻辑合理",
                    affected_elements=["plot_consistency"]
                ))

        return issues

    def _check_plot_progression(self, content: str, chapter_number: int) -> List[ConsistencyIssue]:
        """Check if plot is progressing."""
        issues = []

        # Check for stagnation - too many similar events
        recent_events = [e for e in self.events if e["chapter"] == chapter_number]
        if len(recent_events) > 10:
            event_types = [e["type"] for e in recent_events]
            if event_types.count(event_types[0]) / len(event_types) > 0.7:
                issues.append(ConsistencyIssue(
                    level=ConsistencyLevel.WARNING,
                    category="plot",
                    description="本章事件类型较为单一，可能影响阅读体验",
                    suggestion="考虑增加情节变化或转折",
                    affected_elements=["plot_progression"]
                ))

        return issues


class ConsistencyChecker:
    """
    Main consistency checker that combines all checking mechanisms.

    This is the primary interface for consistency checking.
    """

    def __init__(self, settings: ExtractedSettings):
        """
        Initialize the consistency checker.

        Args:
            settings: Story settings to check against
        """
        self.settings = settings
        self.character_tracker = CharacterTracker(settings.characters)
        self.world_checker = WorldRuleChecker(settings.world)
        self.plot_checker = PlotConsistencyChecker(settings.plot) if settings.plot else None

    def check_content(self,
                     content: str,
                     chapter_number: int,
                     previous_content: str = "") -> ConsistencyReport:
        """
        Check content for consistency issues.

        Args:
            content: Content to check
            chapter_number: Current chapter number
            previous_content: Previous chapter content for context

        Returns:
            ConsistencyReport with all issues found
        """
        report = ConsistencyReport()

        # Check character consistency
        char_issues = self.character_tracker.update_from_content(content, chapter_number)
        for issue in char_issues:
            report.add_issue(issue)

        # Check world consistency
        world_issues = self.world_checker.check_content(content, chapter_number)
        for issue in world_issues:
            report.add_issue(issue)

        # Check plot consistency
        if self.plot_checker:
            plot_issues = self.plot_checker.check_content(
                content, chapter_number, previous_content
            )
            for issue in plot_issues:
                report.add_issue(issue)

        # Calculate final score
        report.calculate_score()

        return report

    def check_full_story(self, chapters: List[Tuple[int, str]]) -> ConsistencyReport:
        """
        Check consistency across multiple chapters.

        Args:
            chapters: List of (chapter_number, content) tuples

        Returns:
            ConsistencyReport for all chapters
        """
        report = ConsistencyReport()
        previous_content = ""

        for num, content in sorted(chapters):
            chapter_report = self.check_content(content, num, previous_content)
            report.issues.extend(chapter_report.issues)
            previous_content = content

        report.calculate_score()
        return report

    def get_character_states(self) -> Dict[str, Dict[str, Any]]:
        """Get current states of all characters."""
        return self.character_tracker.character_states.copy()

    def get_established_locations(self) -> Set[str]:
        """Get all established locations."""
        return self.world_checker.locations.copy()


def create_consistency_checker(settings: ExtractedSettings) -> ConsistencyChecker:
    """
    Factory function to create consistency checkers.

    Args:
        settings: Story settings

    Returns:
        Configured ConsistencyChecker
    """
    return ConsistencyChecker(settings)
