"""
Conversational Setting Extraction Module

This module provides functionality for extracting and managing story settings
through natural conversation. It allows users to gradually build character
profiles, world settings, plot elements, and style preferences through dialogue
rather than filling out complex forms.

Key Features:
- Intent recognition (create/modify/query/settings/chat)
- Rule-based setting extraction from natural language
- Completeness checking with prioritized missing info
- Intelligent question generation for data collection
- Conflict detection and resolution suggestions
- Memory system integration for persistent storage

Example Usage:
    >>> from src.story.setting_extractor import (
    ...     SettingExtractor, IntentRecognizer,
    ...     CompletenessChecker, QuestionGenerator,
    ...     ConflictDetector, MemorySystemIntegrator
    ... )
    >>> from src.story.setting_extractor.models import ExtractionRequest
    >>>
    >>> # Create components
    >>> recognizer = KeywordIntentRecognizer()
    >>> extractor = RuleBasedExtractor()
    >>> checker = BasicCompletenessChecker()
    >>> question_gen = PriorityQuestionGenerator()
    >>> conflict_detector = BasicConflictDetector()
    >>>
    >>> # Process user input
    >>> request = ExtractionRequest(user_input="我想创建一个叫小明的主角")
    >>> intent, types = recognizer.recognize(request.user_input)
    >>> result = extractor.extract(request)
    >>>
    >>> # Check completeness and generate questions
    >>> missing = checker.check_completeness(result.extracted_settings)
    >>> questions = question_gen.generate_questions(
    ...     result.extracted_settings, missing, count=3
    ... )
"""

# Version
__version__ = "0.1.0"
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
    BasicCompletenessChecker
)

from .question_generator import (
    QuestionGenerator,
    PriorityQuestionGenerator
)

from .conflict_detector import (
    ConflictDetector,
    BasicConflictDetector
)

from .utils import MemorySystemIntegrator

# Public API exports
__all__ = [
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
    "QuestionGenerator",
    "PriorityQuestionGenerator",
    "ConflictDetector",
    "BasicConflictDetector",
    "MemorySystemIntegrator"
]

# Module-level convenience function
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
