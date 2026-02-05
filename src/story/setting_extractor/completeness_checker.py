"""
Completeness checking for story settings.

This module provides functionality to check if story settings are complete
and internally evaluate readiness for creation (IMPLICIT MODE).

In implicit mode, missing information is auto-completed by AI rather than
explicitly asking the user. The user should never see "missing info" prompts.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType, MissingInfo
)


class CompletenessChecker(ABC):
    """
    Abstract base class for completeness checkers.

    Completeness checkers analyze extracted settings to identify
    missing information and generate structured missing info reports.
    """

    @abstractmethod
    def check_completeness(self, settings: ExtractedSettings) -> List[MissingInfo]:
        """
        Check settings completeness and identify missing information.

        Args:
            settings: Extracted settings to check

        Returns:
            List of MissingInfo describing what's missing
        """
        pass


@dataclass
class ReadinessAssessment:
    """Assessment of whether settings are ready for creation."""
    is_ready: bool
    readiness_score: float  # 0.0 to 1.0
    missing_critical: List[str] = field(default_factory=list)
    auto_completable: List[str] = field(default_factory=list)
    recommended_action: str = ""
    min_completeness_threshold: float = 0.3

    def to_dict(self) -> Dict:
        return {
            "is_ready": self.is_ready,
            "readiness_score": self.readiness_score,
            "missing_critical": self.missing_critical,
            "auto_completable": self.auto_completable,
            "recommended_action": self.recommended_action
        }


class BasicCompletenessChecker(CompletenessChecker):
    """
    Basic completeness checker with predefined field requirements.

    IMPLICIT MODE: This checker now evaluates readiness for creation
    internally. Missing information is tagged for auto-completion rather
    than user prompting.
    """

    # Required fields for each setting type with metadata
    # Format: (field_name, priority, description, question_template)
    CHARACTER_FIELDS = {
        "name": (1, "Character name", "What is the character's name?"),
        "role": (2, "Character role", "What role does {name} play in the story?"),
        "personality": (2, "Personality traits", "How would you describe {name}'s personality?"),
        "background": (3, "Background story", "What is {name}'s background or history?"),
        "appearance": (3, "Physical appearance", "What does {name} look like?"),
        "abilities": (4, "Special abilities or skills", "What special abilities or skills does {name} have?"),
        "relationships": (4, "Relationships with other characters", "Who are the important people in {name}'s life?")
    }

    WORLD_FIELDS = {
        "world_type": (1, "World type", "What kind of world is the story set in? (fantasy, sci-fi, contemporary, etc.)"),
        "era": (2, "Time period/era", "What time period or era is the story set in?"),
        "geography": (3, "Geography or locations", "What are the important geographical features or locations?"),
        "magic_system": (3, "Magic system (if applicable)", "How does magic work in this world? (if applicable)"),
        "technology_level": (3, "Technology level", "What is the technology level in this world?"),
        "rules": (4, "World rules", "What are the important rules that govern this world?"),
        "factions": (4, "Factions or groups", "What are the major factions or groups in this world?")
    }

    PLOT_FIELDS = {
        "inciting_incident": (1, "Inciting incident", "What event starts the story?"),
        "conflict": (1, "Main conflict", "What is the main conflict or driving force of the story?"),
        "climax": (2, "Story climax", "What is the climactic moment of the story?"),
        "resolution": (2, "Story resolution", "How does the story resolve?"),
        "themes": (3, "Story themes", "What are the main themes or messages of the story?"),
        "rising_action": (3, "Plot developments", "What are the key plot developments leading to the climax?")
    }

    STYLE_FIELDS = {
        "pov": (1, "Point of view", "What point of view should the story use? (first person, third person limited/omniscient)"),
        "writing_style": (2, "Writing style", "What writing style do you prefer? (formal, casual, poetic, etc.)"),
        "tone": (2, "Story tone", "What tone should the story have? (serious, humorous, dark, light, etc.)"),
        "pacing": (3, "Story pacing", "What pacing do you prefer? (fast, medium, slow)"),
        "tense": (3, "Narrative tense", "What tense should the story be written in? (past, present)")
    }

    def __init__(self, require_all_characters: bool = False,
                 implicit_mode: bool = True,
                 min_readiness: float = 0.3):
        """
        Initialize the basic completeness checker.

        Args:
            require_all_characters: If True, check completeness for ALL characters.
                                    If False, only check the first character (default).
            implicit_mode: If True, operate in implicit mode (auto-complete missing
                          info rather than prompting user). Default: True.
            min_readiness: Minimum readiness score (0.0-1.0) to allow creation.
        """
        self.require_all_characters = require_all_characters
        self.implicit_mode = implicit_mode
        self.min_readiness = min_readiness

    def check_completeness(self, settings: ExtractedSettings) -> List[MissingInfo]:
        """
        Check settings completeness and identify missing information.

        This method checks all setting types and generates MissingInfo
        entries for each missing or incomplete field.

        Args:
            settings: Extracted settings to check

        Returns:
            List of MissingInfo sorted by priority (1=highest)
        """
        missing_info = []

        # Check characters
        characters_to_check = settings.characters if self.require_all_characters else settings.characters[:1]
        for character in characters_to_check:
            missing_info.extend(self._check_character(character))

        # Check world setting (if exists)
        if settings.world:
            missing_info.extend(self._check_world(settings.world))
        else:
            # World setting itself is missing
            missing_info.append(MissingInfo(
                setting_type=SettingType.WORLD,
                field_name="world",
                description="World setting",
                priority=1,
                suggested_question="What kind of world is your story set in? Please describe the world, time period, and any special features."
            ))

        # Check plot (if exists)
        if settings.plot:
            missing_info.extend(self._check_plot(settings.plot))
        else:
            # Plot itself is missing
            missing_info.append(MissingInfo(
                setting_type=SettingType.PLOT,
                field_name="plot",
                description="Plot elements",
                priority=1,
                suggested_question="What is the main plot of your story? What's the conflict that drives the story forward?"
            ))

        # Check style (if exists)
        if settings.style:
            missing_info.extend(self._check_style(settings.style))
        else:
            # Style itself is missing
            missing_info.append(MissingInfo(
                setting_type=SettingType.STYLE,
                field_name="style",
                description="Style preferences",
                priority=2,
                suggested_question="What writing style and tone do you prefer for this story?"
            ))

        # Sort by priority (lower number = higher priority)
        missing_info.sort(key=lambda m: m.priority)

        return missing_info

    def _check_character(self, character: CharacterProfile) -> List[MissingInfo]:
        """Check completeness of a character profile."""
        missing = []

        for field_name, (priority, description, question_template) in self.CHARACTER_FIELDS.items():
            # Check if field is missing or empty
            field_value = getattr(character, field_name, None)

            if self._is_field_missing(field_value):
                # Generate question with character name if available
                question = question_template.format(
                    name=character.name or "this character"
                )

                missing.append(MissingInfo(
                    setting_type=SettingType.CHARACTER,
                    field_name=field_name,
                    description=description,
                    priority=priority,
                    suggested_question=question,
                    character_name=character.name
                ))

        return missing

    def _check_world(self, world: WorldSetting) -> List[MissingInfo]:
        """Check completeness of world setting."""
        missing = []

        for field_name, (priority, description, question) in self.WORLD_FIELDS.items():
            field_value = getattr(world, field_name, None)

            if self._is_field_missing(field_value):
                missing.append(MissingInfo(
                    setting_type=SettingType.WORLD,
                    field_name=field_name,
                    description=description,
                    priority=priority,
                    suggested_question=question
                ))

        return missing

    def _check_plot(self, plot: PlotElement) -> List[MissingInfo]:
        """Check completeness of plot elements."""
        missing = []

        for field_name, (priority, description, question) in self.PLOT_FIELDS.items():
            field_value = getattr(plot, field_name, None)

            if self._is_field_missing(field_value):
                missing.append(MissingInfo(
                    setting_type=SettingType.PLOT,
                    field_name=field_name,
                    description=description,
                    priority=priority,
                    suggested_question=question
                ))

        return missing

    def _check_style(self, style: StylePreference) -> List[MissingInfo]:
        """Check completeness of style preferences."""
        missing = []

        for field_name, (priority, description, question) in self.STYLE_FIELDS.items():
            field_value = getattr(style, field_name, None)

            if self._is_field_missing(field_value):
                missing.append(MissingInfo(
                    setting_type=SettingType.STYLE,
                    field_name=field_name,
                    description=description,
                    priority=priority,
                    suggested_question=question
                ))

        return missing

    def _is_field_missing(self, value: any) -> bool:
        """
        Check if a field value is missing or empty.

        Args:
            value: The field value to check

        Returns:
            True if the field is missing/empty, False otherwise
        """
        if value is None:
            return True

        if isinstance(value, str):
            return len(value.strip()) == 0

        if isinstance(value, list):
            return len(value) == 0

        return False

    def is_ready_for_creation(self, settings: ExtractedSettings) -> ReadinessAssessment:
        """
        Assess if settings are ready for story creation (IMPLICIT MODE).

        In implicit mode, we don't require all fields to be filled.
        We only need minimal information and can auto-complete the rest.

        Minimal requirements:
        - At least 1 character (can be unnamed, will be auto-named)
        - Some indication of story context (world, plot, or from conversation)
        - Style will use defaults if not specified

        Args:
            settings: Extracted settings to assess

        Returns:
            ReadinessAssessment with detailed evaluation
        """
        missing_critical = []
        auto_completable = []

        # Check characters
        if not settings.characters:
            # No characters at all - this is critical
            missing_critical.append("characters")
        else:
            # Have characters - check what's missing (for auto-completion)
            for char in settings.characters[:1]:  # Check first character
                for field_name in self.CHARACTER_FIELDS.keys():
                    if self._is_field_missing(getattr(char, field_name, None)):
                        auto_completable.append(f"character.{field_name}")

        # Check world
        if not settings.world or settings.world.is_empty():
            # No world info - can infer from other context
            auto_completable.append("world")
        else:
            for field_name in self.WORLD_FIELDS.keys():
                if settings.world and self._is_field_missing(getattr(settings.world, field_name, None)):
                    auto_completable.append(f"world.{field_name}")

        # Check plot
        if not settings.plot or settings.plot.is_empty():
            # No plot info - can generate default
            auto_completable.append("plot")
        else:
            for field_name in self.PLOT_FIELDS.keys():
                if settings.plot and self._is_field_missing(getattr(settings.plot, field_name, None)):
                    auto_completable.append(f"plot.{field_name}")

        # Check style (can always use defaults)
        if not settings.style or settings.style.is_empty():
            auto_completable.append("style")
        else:
            for field_name in self.STYLE_FIELDS.keys():
                if settings.style and self._is_field_missing(getattr(settings.style, field_name, None)):
                    auto_completable.append(f"style.{field_name}")

        # Calculate readiness score
        total_fields = (
            len(self.CHARACTER_FIELDS) +
            len(self.WORLD_FIELDS) +
            len(self.PLOT_FIELDS) +
            len(self.STYLE_FIELDS)
        )
        readiness_score = 1.0 - (len(auto_completable) + len(missing_critical)) / max(total_fields, 1)
        readiness_score = max(0.0, min(1.0, readiness_score))

        # Adjust score for having ANY information (bonus for implicit mode)
        if len(settings.characters) > 0:
            readiness_score += 0.2
        if settings.world and not settings.world.is_empty():
            readiness_score += 0.1
        if settings.plot and not settings.plot.is_empty():
            readiness_score += 0.1

        readiness_score = min(1.0, readiness_score)

        # Determine if ready
        is_ready = readiness_score >= self.min_readiness and len(missing_critical) == 0

        # Generate recommended action
        if is_ready:
            recommended_action = "proceed_with_auto_completion"
        elif len(missing_critical) > 0:
            recommended_action = f"need_critical_info: {', '.join(missing_critical)}"
        else:
            recommended_action = "gather_more_context"

        return ReadinessAssessment(
            is_ready=is_ready,
            readiness_score=readiness_score,
            missing_critical=missing_critical,
            auto_completable=auto_completable,
            recommended_action=recommended_action,
            min_completeness_threshold=self.min_readiness
        )

    def get_completeness_score(self, settings: ExtractedSettings) -> float:
        """
        Calculate a completeness score (0.0 to 1.0).

        Args:
            settings: Extracted settings to score

        Returns:
            Completeness score (1.0 = complete, 0.0 = empty)
        """
        missing = self.check_completeness(settings)

        # Count total required fields
        total_fields = (
            len(self.CHARACTER_FIELDS) +
            len(self.WORLD_FIELDS) +
            len(self.PLOT_FIELDS) +
            len(self.STYLE_FIELDS)
        )

        # Calculate score
        if total_fields == 0:
            return 1.0

        score = 1.0 - (len(missing) / total_fields)
        return max(0.0, min(1.0, score))

    def is_minimally_complete(self, settings: ExtractedSettings) -> bool:
        """
        Check if settings have at least the minimal required information.

        Minimal requirements:
        - At least 1 character with name and role
        - World type and era
        - Main conflict
        - POV

        Args:
            settings: Extracted settings to check

        Returns:
            True if minimally complete, False otherwise
        """
        # Check character
        has_character = any(
            c.name and c.role
            for c in settings.characters
        )
        if not has_character:
            return False

        # Check world
        if not settings.world or not (settings.world.world_type and settings.world.era):
            return False

        # Check plot
        if not settings.plot or not settings.plot.conflict:
            return False

        # Check style
        if not settings.style or not settings.style.pov:
            return False

        return True

    def get_internal_completion_tasks(self, settings: ExtractedSettings) -> Dict[str, List[str]]:
        """
        Get list of completion tasks for AI (INTERNAL USE ONLY).

        This returns what needs to be auto-completed rather than
        what to ask the user. Used by AISettingCompleter.

        Args:
            settings: Current settings to analyze

        Returns:
            Dictionary mapping setting types to fields needing completion
        """
        tasks = {
            "character": [],
            "world": [],
            "plot": [],
            "style": []
        }

        # Check characters
        for char in settings.characters[:1] if settings.characters else []:
            for field_name in self.CHARACTER_FIELDS.keys():
                if self._is_field_missing(getattr(char, field_name, None)):
                    tasks["character"].append(field_name)

        # If no characters, add as a task
        if not settings.characters:
            tasks["character"].append("create_default")

        # Check world
        if settings.world:
            for field_name in self.WORLD_FIELDS.keys():
                if self._is_field_missing(getattr(settings.world, field_name, None)):
                    tasks["world"].append(field_name)
        else:
            tasks["world"].append("create_default")

        # Check plot
        if settings.plot:
            for field_name in self.PLOT_FIELDS.keys():
                if self._is_field_missing(getattr(settings.plot, field_name, None)):
                    tasks["plot"].append(field_name)
        else:
            tasks["plot"].append("create_default")

        # Check style
        if settings.style:
            for field_name in self.STYLE_FIELDS.keys():
                if self._is_field_missing(getattr(settings.style, field_name, None)):
                    tasks["style"].append(field_name)
        else:
            tasks["style"].append("use_defaults")

        return tasks

    def needs_auto_completion(self, settings: ExtractedSettings) -> bool:
        """
        Quick check if settings need auto-completion.

        Args:
            settings: Settings to check

        Returns:
            True if auto-completion is recommended
        """
        assessment = self.is_ready_for_creation(settings)
        return len(assessment.auto_completable) > 0
