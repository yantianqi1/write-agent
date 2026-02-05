"""
Conversational Agent for implicit story setting extraction.

This module provides the main agent that orchestrates the entire
implicit setting extraction and completion process.

KEY PHILOSOPHY: The user never sees "settings" or "missing info" prompts.
They just chat naturally, and the AI quietly builds and completes settings
in the background.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

from .models import (
    ExtractedSettings, ExtractionRequest, ExtractionResult,
    UserIntent, SettingType, CharacterProfile
)
from .intent_recognizer import KeywordIntentRecognizer
from .setting_extractor import RuleBasedExtractor
from .completeness_checker import BasicCompletenessChecker, ReadinessAssessment
from .ai_completer import AISettingCompleter, CompletionContext
from .conflict_detector import BasicConflictDetector
from .utils import MemorySystemIntegrator


@dataclass
class AgentResponse:
    """Response from the conversational agent."""
    message: str  # What to say to the user
    should_create: bool = False  # Whether to start creating content
    confidence: float = 0.0  # Confidence in this response
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message": self.message,
            "should_create": self.should_create,
            "confidence": self.confidence,
            "metadata": self.metadata.copy()
        }


@dataclass
class AgentState:
    """Internal state of the conversational agent."""
    current_settings: ExtractedSettings
    conversation_history: List[str] = field(default_factory=list)
    user_messages: List[str] = field(default_factory=list)
    agent_messages: List[str] = field(default_factory=list)
    turn_count: int = 0
    completed_turns: List[str] = field(default_factory=list)
    last_intent: Optional[UserIntent] = None
    creation_started: bool = False

    def add_turn(self, user_msg: str, agent_msg: str) -> None:
        """Add a conversation turn."""
        self.user_messages.append(user_msg)
        self.agent_messages.append(agent_msg)
        self.conversation_history.append(f"User: {user_msg}")
        self.conversation_history.append(f"Agent: {agent_msg}")
        self.turn_count += 1

    def get_recent_context(self, n_turns: int = 3) -> List[str]:
        """Get recent conversation turns."""
        recent_user = self.user_messages[-n_turns:] if self.user_messages else []
        return recent_user


class ConversationalAgent:
    """
    Main conversational agent for implicit story setting extraction.

    This agent:
    1. Recognizes user intent from natural language
    2. Extracts settings implicitly (without asking explicit questions)
    3. Auto-completes missing information intelligently
    4. Decides when to start creating content
    5. Never exposes "settings" or "missing info" to the user

    The user experience is just: chat → see content → chat more → see more content.
    """

    def __init__(self,
                 auto_complete: bool = True,
                 min_readiness: float = 0.3,
                 memory_integrator: Optional[MemorySystemIntegrator] = None):
        """
        Initialize the conversational agent.

        Args:
            auto_complete: Whether to auto-complete missing settings
            min_readiness: Minimum readiness score before creation
            memory_integrator: Optional memory system for persistence
        """
        # Core components
        self.intent_recognizer = KeywordIntentRecognizer()
        self.extractor = RuleBasedExtractor()
        self.completeness_checker = BasicCompletenessChecker(
            implicit_mode=True,
            min_readiness=min_readiness
        )
        self.completer = AISettingCompleter(enable_inference=auto_complete)
        self.conflict_detector = BasicConflictDetector()
        self.memory_integrator = memory_integrator

        # Agent state
        self.state = AgentState(current_settings=ExtractedSettings())

        # Response templates
        self._init_response_templates()

    def _init_response_templates(self) -> None:
        """Initialize response templates for different scenarios."""
        self.templates = {
            "greeting": [
                "你好！我是你的创作助手。想写一个什么样的故事？简单描述一下就行。",
                "嗨！我可以帮你写小说。告诉我你想写什么类型的故事？",
                "你好！很高兴和你一起创作。你的故事大概是关于什么的？"
            ],
            "acknowledge": [
                "明白了",
                "好的",
                "了解了",
                "有想法了",
                "记下了"
            ],
            "ready_to_create": [
                "好的，让我开始写第一章",
                "明白了，开始创作",
                "有灵感了，让我写个开头",
                "好的，这就开始"
            ],
            "continue": [
                "继续",
                "接着写",
                "好的，继续创作"
            ],
            "modify_ack": [
                "好的，我来调整一下",
                "明白了，稍作修改",
                "好的，这样改更好"
            ],
            "uncertain": [
                "有意思，能多说一点吗？",
                "我想了解更多细节",
                "能不能多描述一点？"
            ]
        }

    def process(self, user_input: str) -> AgentResponse:
        """
        Process user input and generate a response.

        This is the main entry point for the agent. It handles
        the entire flow from input to response.

        Args:
            user_input: User's natural language input

        Returns:
            AgentResponse with message and metadata
        """
        # Add to conversation history
        self.state.user_messages.append(user_input)
        self.state.turn_count += 1

        # Skip empty input
        if not user_input.strip():
            return self._create_response(
                message="",
                should_create=False,
                confidence=1.0
            )

        # Step 1: Recognize intent
        intent = self.intent_recognizer.recognize(user_input)
        self.state.last_intent = intent

        # Step 2: Handle different intents
        if intent == UserIntent.CHAT:
            return self._handle_chat(user_input)
        elif intent == UserIntent.QUERY:
            return self._handle_query(user_input)
        elif intent == UserIntent.MODIFY:
            return self._handle_modify(user_input)
        elif intent == UserIntent.CREATE or intent == UserIntent.SETTING:
            return self._handle_create_or_setting(user_input, intent)

        # Default: treat as create/setting
        return self._handle_create_or_setting(user_input, UserIntent.CREATE)

    def _handle_create_or_setting(self, user_input: str,
                                  intent: UserIntent) -> AgentResponse:
        """Handle create or setting intent."""
        # Step 1: Extract settings from user input
        request = ExtractionRequest(
            user_input=user_input,
            existing_settings=self.state.current_settings,
            incremental_mode=True,
            conversation_context=self.state.get_recent_context()
        )

        extraction_result = self.extractor.extract(request)

        # Step 2: Merge with current settings
        self.state.current_settings = self.state.current_settings.merge(
            extraction_result.extracted_settings
        )

        # Step 3: Check for conflicts
        conflicts = self.conflict_detector.detect_conflicts(
            self.state.current_settings
        )

        # Step 4: Assess readiness
        readiness = self.completeness_checker.is_ready_for_creation(
            self.state.current_settings
        )

        # Step 5: Auto-complete if needed
        if readiness.is_ready and self.completer.enable_inference:
            completion_context = CompletionContext(
                existing_settings=self.state.current_settings,
                conversation_snippets=self.state.get_recent_context()
            )

            should_complete, reason = self.completer.should_complete(
                self.state.current_settings, completion_context
            )

            if should_complete:
                original = self.state.current_settings
                self.state.current_settings = self.completer.complete(
                    self.state.current_settings, completion_context
                )

                # Log what was completed (for debugging)
                summary = self.completer.get_completion_summary(
                    original, self.state.current_settings
                )

        # Step 6: Generate response
        if readiness.is_ready and not self.state.creation_started:
            self.state.creation_started = True
            return self._create_response(
                message=self._get_template("ready_to_create"),
                should_create=True,
                confidence=readiness.readiness_score,
                metadata={
                    "readiness_score": readiness.readiness_score,
                    "auto_completed": len(readiness.auto_completable) > 0,
                    "settings": self.state.current_settings.to_dict()
                }
            )
        elif self.state.creation_started:
            # Already creating, just acknowledge and continue
            return self._create_response(
                message=self._get_template("continue"),
                should_create=True,
                confidence=readiness.readiness_score
            )
        else:
            # Not ready yet, acknowledge and encourage more input
            return self._create_response(
                message=self._generate_acknowledgment(user_input),
                should_create=False,
                confidence=readiness.readiness_score,
                metadata={
                    "readiness_score": readiness.readiness_score,
                    "needs_more": True
                }
            )

    def _handle_modify(self, user_input: str) -> AgentResponse:
        """Handle modify intent."""
        # For now, treat modify as create with incremental update
        # This will be enhanced with the ModificationEngine
        return self._handle_create_or_setting(user_input, UserIntent.MODIFY)

    def _handle_query(self, user_input: str) -> AgentResponse:
        """Handle query intent."""
        # Generate a brief summary of current understanding
        settings = self.state.current_settings

        parts = []
        if settings.characters:
            main_char = settings.characters[0]
            char_desc = f"主角: {main_char.name or '暂定'}"
            if main_char.personality:
                char_desc += f"，{main_char.personality}"
            parts.append(char_desc)

        if settings.world and settings.world.world_type:
            parts.append(f"世界观: {settings.world.world_type}")

        if settings.plot and settings.plot.conflict:
            parts.append(f"冲突: {settings.plot.conflict}")

        if parts:
            message = "目前的故事设定：" + "；".join(parts) + "。继续聊还是开始创作？"
        else:
            message = self._get_template("uncertain")

        return self._create_response(
            message=message,
            should_create=False,
            confidence=0.7
        )

    def _handle_chat(self, user_input: str) -> AgentResponse:
        """Handle casual chat."""
        return self._create_response(
            message=self._get_template("acknowledge"),
            should_create=False,
            confidence=0.5
        )

    def _create_response(self,
                        message: str,
                        should_create: bool,
                        confidence: float,
                        metadata: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Create an agent response."""
        if metadata is None:
            metadata = {}

        # Add to agent messages
        self.state.agent_messages.append(message)

        # Persist to memory if available
        if self.memory_integrator:
            self.memory_integrator.store_conversation_turn(
                user_input=self.state.user_messages[-1] if self.state.user_messages else "",
                agent_response=message,
                extracted_settings=self.state.current_settings
            )

        return AgentResponse(
            message=message,
            should_create=should_create,
            confidence=confidence,
            metadata=metadata
        )

    def _get_template(self, template_name: str) -> str:
        """Get a random template response."""
        import random
        templates = self.templates.get(template_name, [""])
        return random.choice(templates)

    def _generate_acknowledgment(self, user_input: str) -> str:
        """Generate a contextual acknowledgment."""
        acknowledgments = self.templates["acknowledge"]
        import random
        base = random.choice(acknowledgments)

        # Add context-specific follow-ups
        if any(kw in user_input.lower() for kw in ["主角", "character", "谁"]):
            base += "，这个主角很有意思"
        elif any(kw in user_input.lower() for kw in ["世界", "背景", "world"]):
            base += "，这个设定不错"

        return base + "。再多告诉我一点你的想法，或者让我开始创作？"

    def get_current_settings(self) -> ExtractedSettings:
        """Get the current extracted settings."""
        return self.state.current_settings

    def get_readiness_assessment(self) -> ReadinessAssessment:
        """Get current readiness assessment."""
        return self.completeness_checker.is_ready_for_creation(
            self.state.current_settings
        )

    def reset(self) -> None:
        """Reset the agent state for a new conversation."""
        self.state = AgentState(current_settings=ExtractedSettings())

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the conversation so far."""
        readiness = self.get_readiness_assessment()

        return {
            "turn_count": self.state.turn_count,
            "creation_started": self.state.creation_started,
            "readiness_score": readiness.readiness_score,
            "is_ready": readiness.is_ready,
            "character_count": len(self.state.current_settings.characters),
            "has_world": self.state.current_settings.world is not None,
            "has_plot": self.state.current_settings.plot is not None,
            "has_style": self.state.current_settings.style is not None
        }


class StreamlinedAgent(ConversationalAgent):
    """
    A more streamlined version of the conversational agent.

    This version has even simpler responses and faster readiness
    determination for a more fluid user experience.
    """

    def __init__(self, min_readiness: float = 0.2, **kwargs):
        """Initialize with lower readiness threshold."""
        # Remove min_readiness from kwargs if present to avoid duplicate
        kwargs.pop('min_readiness', None)
        super().__init__(min_readiness=min_readiness, **kwargs)

    def _generate_acknowledgment(self, user_input: str) -> str:
        """Generate simpler acknowledgment."""
        import random
        responses = [
            "嗯，有想法了。继续说说，或者让我开始写？",
            "明白了。还想补充什么吗？",
            "好的。继续聊或者直接开始创作都行。"
        ]
        return random.choice(responses)


def create_agent(agent_type: str = "default",
                auto_complete: bool = True,
                min_readiness: float = 0.3) -> ConversationalAgent:
    """
    Factory function to create different types of agents.

    Args:
        agent_type: Type of agent ("default" or "streamlined")
        auto_complete: Whether to enable auto-completion
        min_readiness: Minimum readiness before creation

    Returns:
        Configured ConversationalAgent instance
    """
    if agent_type == "streamlined":
        return StreamlinedAgent(
            auto_complete=auto_complete,
            min_readiness=min_readiness
        )
    return ConversationalAgent(
        auto_complete=auto_complete,
        min_readiness=min_readiness
    )
