"""
Data models for conversational setting extraction module.

This module defines all core data structures used for extracting,
managing, and validating story settings through natural conversation.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class UserIntent(Enum):
    """User's intent in the conversation."""
    CREATE = "create"      # Creating new settings
    MODIFY = "modify"      # Modifying existing settings
    QUERY = "query"        # Querying current settings
    SETTING = "setting"    # Setting configuration
    CHAT = "chat"          # Casual chat unrelated to settings


class SettingType(Enum):
    """Types of story settings."""
    CHARACTER = "character"  # Character profiles
    WORLD = "world"          # World building
    PLOT = "plot"            # Plot elements
    STYLE = "style"          # Writing style preferences


class ConflictSeverity(Enum):
    """Severity level of setting conflicts."""
    LOW = "low"        # Minor inconsistency, can be ignored
    MEDIUM = "medium"  # Needs clarification
    HIGH = "high"      # Critical conflict, must be resolved


@dataclass
class CharacterProfile:
    """Character profile with detailed attributes."""
    name: Optional[str] = None
    personality: Optional[str] = None
    background: Optional[str] = None
    relationships: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    appearance: Optional[str] = None
    age: Optional[int] = None
    role: Optional[str] = None  # Protagonist, antagonist, supporting, etc.

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "personality": self.personality,
            "background": self.background,
            "relationships": self.relationships.copy(),
            "abilities": self.abilities.copy(),
            "appearance": self.appearance,
            "age": self.age,
            "role": self.role
        }

    def merge(self, other: 'CharacterProfile') -> 'CharacterProfile':
        """
        Merge another CharacterProfile into this one.

        Strategy: New values take precedence, lists are merged with duplicates removed.
        """
        return CharacterProfile(
            name=other.name or self.name,
            personality=other.personality or self.personality,
            background=other.background or self.background,
            relationships=list(set(self.relationships + other.relationships)),
            abilities=list(set(self.abilities + other.abilities)),
            appearance=other.appearance or self.appearance,
            age=other.age if other.age is not None else self.age,
            role=other.role or self.role
        )

    def is_empty(self) -> bool:
        """Check if the profile has any meaningful data."""
        return all([
            self.name is None,
            self.personality is None,
            self.background is None,
            len(self.relationships) == 0,
            len(self.abilities) == 0,
            self.appearance is None,
            self.age is None,
            self.role is None
        ])


@dataclass
class WorldSetting:
    """World building and setting details."""
    world_type: Optional[str] = None  # Fantasy, sci-fi, contemporary, historical, etc.
    era: Optional[str] = None  # Time period/era
    magic_system: Optional[str] = None  # Magic system rules (if applicable)
    technology_level: Optional[str] = None  # Technology level
    geography: Optional[str] = None  # World geography
    locations: List[str] = field(default_factory=list)  # Important locations
    rules: List[str] = field(default_factory=list)  # World rules
    factions: List[str] = field(default_factory=list)  # Political/social factions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "world_type": self.world_type,
            "era": self.era,
            "magic_system": self.magic_system,
            "technology_level": self.technology_level,
            "geography": self.geography,
            "locations": self.locations.copy(),
            "rules": self.rules.copy(),
            "factions": self.factions.copy()
        }

    def merge(self, other: 'WorldSetting') -> 'WorldSetting':
        """Merge another WorldSetting into this one."""
        return WorldSetting(
            world_type=other.world_type or self.world_type,
            era=other.era or self.era,
            magic_system=other.magic_system or self.magic_system,
            technology_level=other.technology_level or self.technology_level,
            geography=other.geography or self.geography,
            locations=list(set(self.locations + other.locations)),
            rules=list(set(self.rules + other.rules)),
            factions=list(set(self.factions + other.factions))
        )

    def is_empty(self) -> bool:
        """Check if the setting has any meaningful data."""
        return all([
            self.world_type is None,
            self.era is None,
            self.magic_system is None,
            self.technology_level is None,
            self.geography is None,
            len(self.locations) == 0,
            len(self.rules) == 0,
            len(self.factions) == 0
        ])


@dataclass
class PlotElement:
    """Plot and story structure elements."""
    inciting_incident: Optional[str] = None  # What starts the story
    conflict: Optional[str] = None  # Main conflict
    rising_action: List[str] = field(default_factory=list)  # Plot developments
    climax: Optional[str] = None  # Story climax
    resolution: Optional[str] = None  # Story resolution
    themes: List[str] = field(default_factory=list)  # Story themes
    subplot_points: List[str] = field(default_factory=list)  # Subplot elements

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "inciting_incident": self.inciting_incident,
            "conflict": self.conflict,
            "rising_action": self.rising_action.copy(),
            "climax": self.climax,
            "resolution": self.resolution,
            "themes": self.themes.copy(),
            "subplot_points": self.subplot_points.copy()
        }

    def merge(self, other: 'PlotElement') -> 'PlotElement':
        """Merge another PlotElement into this one."""
        return PlotElement(
            inciting_incident=other.inciting_incident or self.inciting_incident,
            conflict=other.conflict or self.conflict,
            rising_action=list(set(self.rising_action + other.rising_action)),
            climax=other.climax or self.climax,
            resolution=other.resolution or self.resolution,
            themes=list(set(self.themes + other.themes)),
            subplot_points=list(set(self.subplot_points + other.subplot_points))
        )

    def is_empty(self) -> bool:
        """Check if the plot element has any meaningful data."""
        return all([
            self.inciting_incident is None,
            self.conflict is None,
            len(self.rising_action) == 0,
            self.climax is None,
            self.resolution is None,
            len(self.themes) == 0,
            len(self.subplot_points) == 0
        ])


@dataclass
class StylePreference:
    """Writing style and narrative preferences."""
    writing_style: Optional[str] = None  # Formal, casual, poetic, etc.
    pov: Optional[str] = None  # First person, third person limited/omniscient
    tone: Optional[str] = None  # Serious, humorous, dark, light
    pacing: Optional[str] = None  # Fast, medium, slow
    tense: Optional[str] = None  # Past tense, present tense
    genre: List[str] = field(default_factory=list)  # Genre tags

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "writing_style": self.writing_style,
            "pov": self.pov,
            "tone": self.tone,
            "pacing": self.pacing,
            "tense": self.tense,
            "genre": self.genre.copy()
        }

    def merge(self, other: 'StylePreference') -> 'StylePreference':
        """Merge another StylePreference into this one."""
        return StylePreference(
            writing_style=other.writing_style or self.writing_style,
            pov=other.pov or self.pov,
            tone=other.tone or self.tone,
            pacing=other.pacing or self.pacing,
            tense=other.tense or self.tense,
            genre=list(set(self.genre + other.genre))
        )

    def is_empty(self) -> bool:
        """Check if the style preference has any meaningful data."""
        return all([
            self.writing_style is None,
            self.pov is None,
            self.tone is None,
            self.pacing is None,
            self.tense is None,
            len(self.genre) == 0
        ])


@dataclass
class ExtractedSettings:
    """
    Container for all extracted story settings.

    This is the main data structure that holds all settings extracted
    from user conversations. It supports incremental updates through
    the merge() method.
    """
    characters: List[CharacterProfile] = field(default_factory=list)
    world: Optional[WorldSetting] = None
    plot: Optional[PlotElement] = None
    style: Optional[StylePreference] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "characters": [c.to_dict() for c in self.characters],
            "world": self.world.to_dict() if self.world else None,
            "plot": self.plot.to_dict() if self.plot else None,
            "style": self.style.to_dict() if self.style else None
        }

    def merge(self, other: 'ExtractedSettings') -> 'ExtractedSettings':
        """
        Merge another ExtractedSettings into this one.

        Strategy:
        - Characters: merged by name if names match, otherwise appended
        - World/Plot/Style: shallow merge (new values take precedence)
        """
        # Merge characters by name
        merged_chars = self.characters.copy()
        for other_char in other.characters:
            if other_char.name:
                # Look for existing character with same name
                existing = next(
                    (c for c in merged_chars if c.name == other_char.name),
                    None
                )
                if existing:
                    # Merge into existing character
                    idx = merged_chars.index(existing)
                    merged_chars[idx] = existing.merge(other_char)
                else:
                    # Add new character
                    merged_chars.append(other_char)
            else:
                # Character without name, just append
                merged_chars.append(other_char)

        # Merge world settings
        merged_world = self.world
        if other.world:
            if self.world:
                merged_world = self.world.merge(other.world)
            else:
                merged_world = other.world

        # Merge plot elements
        merged_plot = self.plot
        if other.plot:
            if self.plot:
                merged_plot = self.plot.merge(other.plot)
            else:
                merged_plot = other.plot

        # Merge style preferences
        merged_style = self.style
        if other.style:
            if self.style:
                merged_style = self.style.merge(other.style)
            else:
                merged_style = other.style

        return ExtractedSettings(
            characters=merged_chars,
            world=merged_world,
            plot=merged_plot,
            style=merged_style
        )

    def is_empty(self) -> bool:
        """Check if all settings are empty."""
        return (
            len(self.characters) == 0 and
            (self.world is None or self.world.is_empty()) and
            (self.plot is None or self.plot.is_empty()) and
            (self.style is None or self.style.is_empty())
        )


@dataclass
class MissingInfo:
    """Information about missing setting fields."""
    setting_type: SettingType  # Which setting type
    field_name: str  # Name of the missing field
    description: str  # Human-readable description
    priority: int  # Priority (1=highest, 5=lowest)
    suggested_question: str  # Suggested question to ask user
    character_name: Optional[str] = None  # For character-specific fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "setting_type": self.setting_type.value,
            "field_name": self.field_name,
            "description": self.description,
            "priority": self.priority,
            "suggested_question": self.suggested_question,
            "character_name": self.character_name
        }


@dataclass
class Conflict:
    """Detected conflict between settings."""
    conflict_type: str  # Type of conflict (e.g., "world_type_conflict")
    setting_type: SettingType  # Which setting type has the conflict
    field_name: str  # Field with the conflict
    original_value: Any  # Original value
    new_value: Any  # Conflicting new value
    severity: ConflictSeverity  # How severe is the conflict
    description: str  # Human-readable conflict description
    resolution_suggestion: str  # Suggested way to resolve
    character_name: Optional[str] = None  # For character-specific conflicts

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "conflict_type": self.conflict_type,
            "setting_type": self.setting_type.value,
            "field_name": self.field_name,
            "original_value": self.original_value,
            "new_value": self.new_value,
            "severity": self.severity.value,
            "description": self.description,
            "resolution_suggestion": self.resolution_suggestion,
            "character_name": self.character_name
        }


@dataclass
class ExtractionRequest:
    """Request to extract settings from user input."""
    user_input: str  # User's natural language input
    existing_settings: Optional[ExtractedSettings] = None  # Current settings for merge
    incremental_mode: bool = True  # Whether to merge with existing settings
    conversation_context: Optional[List[str]] = None  # Previous conversation turns

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "user_input": self.user_input,
            "existing_settings": self.existing_settings.to_dict() if self.existing_settings else None,
            "incremental_mode": self.incremental_mode,
            "conversation_context": self.conversation_context.copy() if self.conversation_context else []
        }


@dataclass
class ExtractionResult:
    """Result of setting extraction process."""
    extracted_settings: ExtractedSettings  # Extracted/merged settings
    detected_intent: UserIntent  # User's detected intent
    involved_types: List[SettingType]  # Which setting types were involved
    missing_info: List[MissingInfo]  # Information that's still missing
    conflicts: List[Conflict]  # Detected conflicts
    suggested_questions: List[str]  # Follow-up questions to ask
    confidence: float  # Confidence score (0.0 to 1.0)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Additional metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "extracted_settings": self.extracted_settings.to_dict(),
            "detected_intent": self.detected_intent.value,
            "involved_types": [t.value for t in self.involved_types],
            "missing_info": [m.to_dict() for m in self.missing_info],
            "conflicts": [c.to_dict() for c in self.conflicts],
            "suggested_questions": self.suggested_questions.copy(),
            "confidence": self.confidence,
            "metadata": self.metadata.copy()
        }

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues (high severity conflicts)."""
        return any(c.severity == ConflictSeverity.HIGH for c in self.conflicts)

    def get_missing_by_priority(self, max_priority: int = 3) -> List[MissingInfo]:
        """Get missing info filtered by priority (lower number = higher priority)."""
        return [m for m in self.missing_info if m.priority <= max_priority]
