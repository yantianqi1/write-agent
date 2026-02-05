"""
Creation decision engine.

This module decides WHEN and HOW to create story content.
It evaluates readiness, selects strategies, and manages the
creation flow without exposing decisions to the user.

KEY PHILOSOPHY: The user just chats and sees content appear.
All decision-making happens transparently.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..setting_extractor.models import ExtractedSettings
from ..setting_extractor.completeness_checker import ReadinessAssessment


class CreationStrategy(Enum):
    """Strategy for content generation."""
    CONTINUE = "continue"  # Continue from where we left off
    EXPAND = "expand"  # Expand on a specific scene or idea
    REWRITE = "rewrite"  # Rewrite existing content
    OUTLINE = "outline"  # Generate/review outline first
    FULL = "full"  # Generate complete content


class CreationTrigger(Enum):
    """What triggered the creation decision."""
    EXPLICIT_REQUEST = "explicit"  # User explicitly asked to create
    READINESS_THRESHOLD = "readiness"  # Settings reached readiness threshold
    USER_CONTINUE = "continue"  # User said "continue"
    MODIFY_COMPLETE = "modify_complete"  # Modification done, resume creation


@dataclass
class CreationDecision:
    """Decision about whether and how to create content."""
    should_create: bool
    strategy: CreationStrategy
    trigger: CreationTrigger
    confidence: float  # 0.0 to 1.0
    reason: str
    suggested_chapter: Optional[int] = None
    suggested_length: int = 1000  # Target word count
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "should_create": self.should_create,
            "strategy": self.strategy.value,
            "trigger": self.trigger.value,
            "confidence": self.confidence,
            "reason": self.reason,
            "suggested_chapter": self.suggested_chapter,
            "suggested_length": self.suggested_length,
            "metadata": self.metadata.copy()
        }


@dataclass
class CreationContext:
    """Context for creation decision."""
    current_settings: ExtractedSettings
    readiness_assessment: ReadinessAssessment
    conversation_turn_count: int
    last_user_message: str
    has_created_before: bool = False
    last_chapter_created: Optional[int] = None
    total_words_created: int = 0
    user_satisfaction_score: float = 0.5


class DecisionEngine(ABC):
    """Abstract base class for creation decision engines."""

    @abstractmethod
    def should_create(self, context: CreationContext) -> CreationDecision:
        """Decide whether to create content now."""
        pass

    @abstractmethod
    def select_strategy(self, context: CreationContext) -> CreationStrategy:
        """Select the appropriate creation strategy."""
        pass


class ThresholdDecisionEngine(DecisionEngine):
    """
    Decision engine based on readiness thresholds.

    This engine starts creation when settings reach a minimum
    readiness threshold, preferring earlier engagement with
    the user over waiting for "perfect" settings.
    """

    def __init__(self,
                 min_readiness: float = 0.3,
                 ideal_readiness: float = 0.6,
                 max_turns_before_force: int = 5):
        """
        Initialize the threshold decision engine.

        Args:
            min_readiness: Minimum readiness score to allow creation
            ideal_readiness: Target readiness score for best experience
            max_turns_before_force: Force creation after this many turns even if not ready
        """
        self.min_readiness = min_readiness
        self.ideal_readiness = ideal_readiness
        self.max_turns_before_force = max_turns_before_force

    def should_create(self, context: CreationContext) -> CreationDecision:
        """
        Decide whether to create content now.

        Args:
            context: Current creation context

        Returns:
            CreationDecision with details
        """
        readiness = context.readiness_assessment
        score = readiness.readiness_score

        # Check for explicit creation requests
        if self._has_explicit_request(context.last_user_message):
            return CreationDecision(
                should_create=True,
                strategy=self.select_strategy(context),
                trigger=CreationTrigger.EXPLICIT_REQUEST,
                confidence=0.95,
                reason="用户明确要求开始创作",
                suggested_chapter=1 if not context.has_created_before else context.last_chapter_created + 1
            )

        # Check for "continue" signals
        if self._has_continue_signal(context.last_user_message) and context.has_created_before:
            return CreationDecision(
                should_create=True,
                strategy=CreationStrategy.CONTINUE,
                trigger=CreationTrigger.USER_CONTINUE,
                confidence=0.95,
                reason="用户要求继续创作",
                suggested_chapter=context.last_chapter_created + 1
            )

        # Check readiness threshold
        if score >= self.ideal_readiness:
            return CreationDecision(
                should_create=True,
                strategy=self.select_strategy(context),
                trigger=CreationTrigger.READINESS_THRESHOLD,
                confidence=score,
                reason=f"设定完整度达到理想水平 ({score:.2f})",
                suggested_chapter=1 if not context.has_created_before else context.last_chapter_created + 1
            )

        # Check minimum threshold (proceed with auto-completion)
        if score >= self.min_readiness:
            # Only proceed if we've had enough conversation
            if context.conversation_turn_count >= 2:
                return CreationDecision(
                    should_create=True,
                    strategy=self.select_strategy(context),
                    trigger=CreationTrigger.READINESS_THRESHOLD,
                    confidence=score,
                    reason=f"设定基本就绪，AI将补全缺失信息后开始创作",
                    suggested_chapter=1 if not context.has_created_before else context.last_chapter_created + 1
                )

        # Force creation after too many turns (don't keep them waiting)
        if context.conversation_turn_count >= self.max_turns_before_force:
            return CreationDecision(
                should_create=True,
                strategy=self.select_strategy(context),
                trigger=CreationTrigger.READINESS_THRESHOLD,
                confidence=0.5,
                reason=f"已收集足够上下文，开始创作",
                suggested_chapter=1 if not context.has_created_before else context.last_chapter_created + 1
            )

        # Not ready yet
        return CreationDecision(
            should_create=False,
            strategy=CreationStrategy.OUTLINE,
            trigger=CreationTrigger.READINESS_THRESHOLD,
            confidence=score,
            reason=f"需要更多信息 (当前完整度: {score:.2f})",
            metadata={"needs_more_input": True}
        )

    def select_strategy(self, context: CreationContext) -> CreationStrategy:
        """
        Select the appropriate creation strategy.

        Args:
            context: Current creation context

        Returns:
            Selected CreationStrategy
        """
        # First creation always use outline + first chapter
        if not context.has_created_before:
            return CreationStrategy.OUTLINE

        # Check for explicit rewrite requests
        if "重写" in context.last_user_message or "rewrite" in context.last_user_message.lower():
            return CreationStrategy.REWRITE

        # Check for expansion requests
        if "扩展" in context.last_user_message or "expand" in context.last_user_message.lower():
            return CreationStrategy.EXPAND

        # Check for continue
        if self._has_continue_signal(context.last_user_message):
            return CreationStrategy.CONTINUE

        # Default: continue
        return CreationStrategy.CONTINUE

    def _has_explicit_request(self, message: str) -> bool:
        """Check if message contains explicit creation request."""
        keywords = [
            "开始", "开始写", "创作", "写一下",
            "开始创作", "开始写", "generate", "write", "create",
            "开始写故事", "让我开始", "开始生成"
        ]
        message_lower = message.lower()
        return any(kw in message_lower or kw in message for kw in keywords)

    def _has_continue_signal(self, message: str) -> bool:
        """Check if message is a continue signal."""
        keywords = [
            "继续", "continue", "next", "下一步",
            "接着写", "写下去", "下一章", "后面呢"
        ]
        message_lower = message.lower()
        return any(kw in message_lower or kw in message for kw in keywords)


class AdaptiveDecisionEngine(ThresholdDecisionEngine):
    """
    Adaptive decision engine that learns from user behavior.

    This engine adjusts its thresholds based on user satisfaction
    and engagement patterns.
    """

    def __init__(self, **kwargs):
        """Initialize the adaptive decision engine."""
        super().__init__(**kwargs)
        self.satisfaction_history: List[float] = []
        self.adjusted_readiness = self.min_readiness

    def update_satisfaction(self, score: float) -> None:
        """
        Update satisfaction history and adjust thresholds.

        Args:
            score: Satisfaction score from last creation (0.0 to 1.0)
        """
        self.satisfaction_history.append(score)

        # Keep only recent history
        if len(self.satisfaction_history) > 10:
            self.satisfaction_history = self.satisfaction_history[-10:]

        # Adjust threshold based on satisfaction
        if len(self.satisfaction_history) >= 3:
            avg_satisfaction = sum(self.satisfaction_history[-3:]) / 3

            if avg_satisfaction > 0.7:
                # High satisfaction: can wait for more info
                self.adjusted_readiness = min(self.ideal_readiness, self.adjusted_readiness + 0.05)
            elif avg_satisfaction < 0.4:
                # Low satisfaction: start creating sooner
                self.adjusted_readiness = max(self.min_readiness, self.adjusted_readiness - 0.05)

    def should_create(self, context: CreationContext) -> CreationDecision:
        """
        Decide whether to create with adaptive threshold.

        Args:
            context: Current creation context

        Returns:
            CreationDecision with adaptive consideration
        """
        # Use adjusted threshold
        original_min = self.min_readiness
        self.min_readiness = self.adjusted_readiness

        decision = super().should_create(context)

        # Restore original
        self.min_readiness = original_min

        # Add metadata about adaptation
        decision.metadata["adjusted_threshold"] = self.adjusted_readiness
        decision.metadata["avg_satisfaction"] = (
            sum(self.satisfaction_history) / len(self.satisfaction_history)
            if self.satisfaction_history else 0.5
        )

        return decision


class CreationFlowManager:
    """
    Manages the overall creation flow and decision orchestration.

    This class coordinates:
    - When to start creating
    - What to create (chapter, scene, etc.)
    - How to respond to user feedback
    """

    def __init__(self, decision_engine: Optional[DecisionEngine] = None):
        """
        Initialize the creation flow manager.

        Args:
            decision_engine: Optional custom decision engine
        """
        self.decision_engine = decision_engine or AdaptiveDecisionEngine()
        self.current_chapter = 0
        self.total_words = 0
        self.creation_history: List[Dict[str, Any]] = []

    def evaluate(self, context: CreationContext) -> CreationDecision:
        """
        Evaluate whether to create content now.

        Args:
            context: Current creation context

        Returns:
            CreationDecision
        """
        decision = self.decision_engine.should_create(context)

        # Update suggested chapter
        if decision.should_create and decision.suggested_chapter is None:
            decision.suggested_chapter = self.current_chapter + 1

        return decision

    def record_creation(self, decision: CreationDecision, word_count: int) -> None:
        """
        Record a creation action for history.

        Args:
            decision: The decision that led to creation
            word_count: Number of words generated
        """
        self.current_chapter = decision.suggested_chapter or (self.current_chapter + 1)
        self.total_words += word_count

        self.creation_history.append({
            "chapter": self.current_chapter,
            "strategy": decision.strategy.value,
            "words": word_count,
            "timestamp": __import__("datetime").datetime.now().isoformat()
        })

    def get_creation_summary(self) -> Dict[str, Any]:
        """Get summary of creations so far."""
        return {
            "current_chapter": self.current_chapter,
            "total_words": self.total_words,
            "creation_count": len(self.creation_history),
            "recent_creations": self.creation_history[-5:] if self.creation_history else []
        }

    def should_continue(self, context: CreationContext) -> bool:
        """
        Quick check if creation should continue.

        Args:
            context: Current creation context

        Returns:
            True if creation should continue
        """
        if not context.has_created_before:
            return False

        # If user explicitly said continue
        if self.decision_engine._has_continue_signal(context.last_user_message):
            return True

        # If we're in a good flow
        if context.readiness_assessment.readiness_score > 0.5:
            return True

        return False

    def suggest_next_action(self, context: CreationContext) -> str:
        """
        Suggest the next action for the agent.

        Args:
            context: Current creation context

        Returns:
            Suggested action description
        """
        if not context.has_created_before:
            if context.readiness_assessment.is_ready:
                return "开始创作第一章"
            else:
                return "继续收集设定信息"

        if context.conversation_turn_count > 0:
            last_msg = context.last_user_message.lower()

            # Check for modifications
            if "更" in last_msg or "改" in last_msg or "change" in last_msg:
                return "应用修改后继续创作"

            # Check for continue
            if self.decision_engine._has_continue_signal(context.last_user_message):
                return f"继续创作第{self.current_chapter + 1}章"

            # Check for new ideas
            if "加个" in last_msg or "增加" in last_msg or "add" in last_msg:
                return "将新想法融入下一章"

        return "继续当前创作流程"


def create_decision_engine(engine_type: str = "adaptive",
                          min_readiness: float = 0.3) -> DecisionEngine:
    """
    Factory function to create decision engines.

    Args:
        engine_type: Type of engine ("threshold" or "adaptive")
        min_readiness: Minimum readiness threshold

    Returns:
        Configured DecisionEngine
    """
    if engine_type == "adaptive":
        return AdaptiveDecisionEngine(min_readiness=min_readiness)
    return ThresholdDecisionEngine(min_readiness=min_readiness)


def create_flow_manager(engine_type: str = "adaptive") -> CreationFlowManager:
    """
    Factory function to create creation flow managers.

    Args:
        engine_type: Type of decision engine to use

    Returns:
        Configured CreationFlowManager
    """
    engine = create_decision_engine(engine_type)
    return CreationFlowManager(decision_engine=engine)
