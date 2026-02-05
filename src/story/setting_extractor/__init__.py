"""
Conversational Setting Extraction Module (IMPLICIT MODE)

This module provides functionality for extracting and managing story settings
through natural conversation in IMPLICIT mode.

KEY PHILOSOPHY: Users never see "settings" or "missing info". They just chat,
and the AI quietly builds and completes settings in the background.

Key Features:
- Intent recognition (create/modify/query/settings/chat)
- Rule-based setting extraction from natural language
- AI-powered auto-completion of missing settings
- Creation decision engine (when to start writing)
- Modification understanding (natural language modification)
- Memory system integration for persistent storage

New Components (v0.2.0):
- ConversationalAgent: Main agent for implicit setting extraction
- AISettingCompleter: Auto-complete missing settings
- ModificationEngine: Understand and apply natural language modifications
- CreationDecisionEngine: Decide when to start creating content
- ReadinessAssessment: Internal evaluation of creation readiness

Example Usage (Implicit Mode):
    >>> from src.story.setting_extractor import create_agent
    >>>
    >>> # Create agent with auto-completion
    >>> agent = create_agent(auto_complete=True, min_readiness=0.3)
    >>>
    >>> # Just chat - settings are extracted implicitly
    >>> response = agent.process("我想写个科幻小说")
    >>> print(response.message)  # "明白了，继续说说..."
    >>>
    >>> response = agent.process("主角是个黑客")
    >>> print(response.should_create)  # May be True now
    >>>
    >>> # Get current settings (internal use only)
    >>> settings = agent.get_current_settings()
"""

# Version
__version__ = "0.2.0"
__author__ = "Story Agent Team"

# Data models
from .models import (
    # Enums
    UserIntent,
    SettingType,
    ConflictSeverity,
    # Data classes
    CharacterProfile,
    WorldSetting,
    PlotElement,
    StylePreference,
    ExtractedSettings,
    MissingInfo,
    Conflict,
    ExtractionRequest,
    ExtractionResult
)

# Core components
from .intent_recognizer import (
    IntentRecognizer,
    KeywordIntentRecognizer
)

from .setting_extractor import (
    SettingExtractor,
    RuleBasedExtractor
)

from .completeness_checker import (
    CompletenessChecker,
    BasicCompletenessChecker,
    ReadinessAssessment
)

from .question_generator import (
    QuestionGenerator,
    PriorityQuestionGenerator,
    PromptGenerator,
    InternalPromptGenerator
)

from .conflict_detector import (
    ConflictDetector,
    BasicConflictDetector
)

from .utils import MemorySystemIntegrator

# New implicit mode components
from .ai_completer import (
    SettingCompleter,
    AISettingCompleter,
    InferenceCompleter,
    HybridCompleter,
    CompletionContext
)

from .conversational_agent import (
    ConversationalAgent,
    StreamlinedAgent,
    AgentResponse,
    AgentState,
    create_agent
)

from .modification_engine import (
    ModificationEngine,
    ModificationParser,
    RuleBasedModificationParser,
    ModificationScope,
    ModificationType,
    ModificationTarget,
    ModificationInstruction,
    ModificationResult,
    create_modification_engine
)

# Public API exports
__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Enums
    "UserIntent",
    "SettingType",
    "ConflictSeverity",

    # Data models
    "CharacterProfile",
    "WorldSetting",
    "PlotElement",
    "StylePreference",
    "ExtractedSettings",
    "MissingInfo",
    "Conflict",
    "ExtractionRequest",
    "ExtractionResult",

    # Core components
    "IntentRecognizer",
    "KeywordIntentRecognizer",
    "SettingExtractor",
    "RuleBasedExtractor",
    "CompletenessChecker",
    "BasicCompletenessChecker",
    "ReadinessAssessment",
    "QuestionGenerator",
    "PriorityQuestionGenerator",
    "ConflictDetector",
    "BasicConflictDetector",
    "MemorySystemIntegrator",

    # New implicit mode components
    "PromptGenerator",
    "InternalPromptGenerator",
    "SettingCompleter",
    "AISettingCompleter",
    "InferenceCompleter",
    "HybridCompleter",
    "CompletionContext",

    "ConversationalAgent",
    "StreamlinedAgent",
    "AgentResponse",
    "AgentState",
    "create_agent",

    "ModificationEngine",
    "ModificationParser",
    "RuleBasedModificationParser",
    "ModificationScope",
    "ModificationType",
    "ModificationTarget",
    "ModificationInstruction",
    "ModificationResult",
    "create_modification_engine",
]

# Module-level convenience functions
def create_extraction_pipeline():
    """
    Create a complete extraction pipeline with all components.

    Returns a tuple of (recognizer, extractor, checker, question_gen, conflict_detector, memory_integrator).

    Example:
        >>> recognizer, extractor, checker, question_gen, conflict_detector, memory_integrator = create_extraction_pipeline()
    """
    recognizer = KeywordIntentRecognizer()
    extractor = RuleBasedExtractor()
    checker = BasicCompletenessChecker()
    question_gen = PriorityQuestionGenerator()
    conflict_detector = BasicConflictDetector()
    memory_integrator = MemorySystemIntegrator()

    return (
        recognizer,
        extractor,
        checker,
        question_gen,
        conflict_detector,
        memory_integrator
    )


def create_implicit_agent(auto_complete: bool = True,
                          min_readiness: float = 0.3,
                          agent_type: str = "default") -> ConversationalAgent:
    """
    Create a conversational agent for implicit setting extraction.

    This is the recommended entry point for the implicit mode.

    Args:
        auto_complete: Enable AI auto-completion of missing settings
        min_readiness: Minimum readiness score before starting creation (0.0-1.0)
        agent_type: Type of agent ("default" or "streamlined")

    Returns:
        Configured ConversationalAgent

    Example:
        >>> agent = create_implicit_agent(auto_complete=True)
        >>> response = agent.process("我想写个关于勇敢骑士的故事")
        >>> if response.should_create:
        ...     print("开始创作！")
    """
    return create_agent(
        agent_type=agent_type,
        auto_complete=auto_complete,
        min_readiness=min_readiness
    )
