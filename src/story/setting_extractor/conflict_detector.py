"""
Conflict detection for story settings.

This module provides functionality to detect contradictions and
conflicts in story settings before they cause problems.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType, Conflict, ConflictSeverity
)


class ConflictDetector(ABC):
    """
    Abstract base class for conflict detectors.

    Conflict detectors analyze settings to identify contradictions
    and conflicts that could cause problems.
    """

    @abstractmethod
    def detect_conflicts(self, settings: ExtractedSettings) -> List[Conflict]:
        """
        Detect conflicts in the given settings.

        Args:
            settings: Extracted settings to check

        Returns:
            List of detected conflicts
        """
        pass


class BasicConflictDetector(ConflictDetector):
    """
    Basic conflict detector using rule-based checks.

    This detector checks for common contradictions in settings:
    - World type conflicts (fantasy vs sci-fi)
    - Era conflicts (ancient vs future)
    - Character personality conflicts (contradictory traits)
    - Style conflicts (inconsistent POV)
    """

    # Mutually exclusive world types
    MUTUALLY_EXCLUSIVE_WORLD_TYPES = {
        "fantasy": ["sci-fi", "science fiction", "contemporary", "modern"],
        "sci-fi": ["fantasy", "historical", "ancient"],
        "historical": ["sci-fi", "future", "modern"],
        "contemporary": ["fantasy", "sci-fi", "historical", "ancient"]
    }

    # Contradictory personality traits
    CONTRADICTORY_TRAITS = {
        "shy": ["outgoing", "extroverted", "bold"],
        "outgoing": ["shy", "introverted", "reserved"],
        "kind": ["cruel", "mean", "evil"],
        "cruel": ["kind", "compassionate", "gentle"],
        "brave": ["cowardly", "fearful"],
        "cowardly": ["brave", "courageous", "bold"],
        "intelligent": ["stupid", "foolish", "dim-witted"],
        "honest": ["dishonest", "deceitful", "lying"]
    }

    # Consistent POV combinations
    CONSISTENT_POV = {
        "first person": ["first person"],
        "third person limited": ["third person limited", "third person"],
        "third person omniscient": ["third person omniscient", "third person"]
    }

    def __init__(self):
        """Initialize the basic conflict detector."""
        pass

    def detect_conflicts(self, settings: ExtractedSettings) -> List[Conflict]:
        """
        Detect conflicts in the given settings.

        This method checks all setting types for conflicts:
        1. World setting conflicts
        2. Character conflicts
        3. Style conflicts
        4. Plot conflicts (basic checks)

        Args:
            settings: Extracted settings to check

        Returns:
            List of detected conflicts (may be empty)
        """
        conflicts = []

        # Check world conflicts
        if settings.world:
            conflicts.extend(self._check_world_conflicts(settings.world))

        # Check character conflicts
        for character in settings.characters:
            conflicts.extend(self._check_character_conflicts(character))

        # Check style conflicts
        if settings.style:
            conflicts.extend(self._check_style_conflicts(settings.style))

        # Check cross-setting conflicts
        conflicts.extend(self._check_cross_setting_conflicts(settings))

        return conflicts

    def _check_world_conflicts(self, world: WorldSetting) -> List[Conflict]:
        """Check for conflicts within world settings."""
        conflicts = []

        # Check for mutually exclusive world types
        if world.world_type:
            world_type_lower = world.world_type.lower()
            for exclusive_type, contradictions in self.MUTUALLY_EXCLUSIVE_WORLD_TYPES.items():
                if exclusive_type in world_type_lower:
                    for contradiction in contradictions:
                        if contradiction in world_type_lower:
                            conflicts.append(Conflict(
                                conflict_type="world_type_conflict",
                                setting_type=SettingType.WORLD,
                                field_name="world_type",
                                original_value=exclusive_type,
                                new_value=contradiction,
                                severity=ConflictSeverity.HIGH,
                                description=f"World type cannot be both '{exclusive_type}' and '{contradiction}'",
                                resolution_suggestion=f"Choose either {exclusive_type} or {contradiction} as the primary world type.",
                                character_name=None
                            ))
                            break

        # Check era conflicts
        if world.era:
            era_lower = world.era.lower()
            # Check for contradictory era indicators
            contradictory_pairs = [
                ("ancient", "future"),
                ("medieval", "modern"),
                ("past", "future"),
                ("historical", "futuristic")
            ]
            for era1, era2 in contradictory_pairs:
                if era1 in era_lower and era2 in era_lower:
                    conflicts.append(Conflict(
                        conflict_type="era_conflict",
                        setting_type=SettingType.WORLD,
                        field_name="era",
                        original_value=era1,
                        new_value=era2,
                        severity=ConflictSeverity.HIGH,
                        description=f"Era cannot be both '{era1}' and '{era2}'",
                        resolution_suggestion=f"Clarify the time period. Is this set in {era1} times or {era2} times?",
                        character_name=None
                    ))
                    break

        return conflicts

    def _check_character_conflicts(self, character: CharacterProfile) -> List[Conflict]:
        """Check for conflicts within character settings."""
        conflicts = []

        # Check personality contradictions
        if character.personality:
            personality_lower = character.personality.lower()
            for trait, contradictions in self.CONTRADICTORY_TRAITS.items():
                if trait in personality_lower:
                    for contradiction in contradictions:
                        if contradiction in personality_lower:
                            conflicts.append(Conflict(
                                conflict_type="personality_conflict",
                                setting_type=SettingType.CHARACTER,
                                field_name="personality",
                                original_value=trait,
                                new_value=contradiction,
                                severity=ConflictSeverity.MEDIUM,
                                description=f"Character {character.name or ''} has contradictory traits: '{trait}' and '{contradiction}'",
                                resolution_suggestion=f"Clarify whether the character is more {trait} or {contradiction}, or describe the nuanced combination.",
                                character_name=character.name
                            ))
                            break

        # Check age vs role consistency (basic check)
        if character.age and character.role:
            role_lower = character.role.lower()
            if character.age < 13 and "protagonist" in role_lower:
                # This might be fine, but flag it
                conflicts.append(Conflict(
                    conflict_type="age_role_consistency",
                    setting_type=SettingType.CHARACTER,
                    field_name="age",
                    original_value=str(character.age),
                    new_value=character.role,
                    severity=ConflictSeverity.LOW,
                    description=f"Character {character.name or ''} is {character.age} years old but is marked as protagonist",
                    resolution_suggestion="This may be intentional (child protagonist), but ensure the age and role are consistent with the story tone.",
                    character_name=character.name
                ))

        return conflicts

    def _check_style_conflicts(self, style: StylePreference) -> List[Conflict]:
        """Check for conflicts within style preferences."""
        conflicts = []

        # Check POV consistency
        if style.pov:
            pov_lower = style.pov.lower()
            # Check for contradictory POV indicators
            if "first" in pov_lower and "third" in pov_lower:
                conflicts.append(Conflict(
                    conflict_type="pov_conflict",
                    setting_type=SettingType.STYLE,
                    field_name="pov",
                    original_value="first person",
                    new_value="third person",
                    severity=ConflictSeverity.HIGH,
                    description=f"POV cannot be both first person and third person",
                    resolution_suggestion="Choose either first person ('I') or third person ('he/she/they') narrative.",
                    character_name=None
                ))

        # Check tense consistency
        if style.tense:
            tense_lower = style.tense.lower()
            if "past" in tense_lower and "present" in tense_lower:
                conflicts.append(Conflict(
                    conflict_type="tense_conflict",
                    setting_type=SettingType.STYLE,
                    field_name="tense",
                    original_value="past tense",
                    new_value="present tense",
                    severity=ConflictSeverity.MEDIUM,
                    description="Tense cannot be both past and present",
                    resolution_suggestion="Choose either past tense ('was') or present tense ('is') for the narrative.",
                    character_name=None
                ))

        # Check tone consistency with genre (basic check)
        if style.tone and style.genre:
            tone_lower = style.tone.lower()
            genre_str = " ".join(style.genre).lower()
            # Dark tone with comedy genre
            if "dark" in tone_lower and "comedy" in genre_str:
                conflicts.append(Conflict(
                    conflict_type="tone_genre_conflict",
                    setting_type=SettingType.STYLE,
                    field_name="tone",
                    original_value="dark",
                    new_value="comedy",
                    severity=ConflictSeverity.LOW,
                    description="Dark tone with comedy genre",
                    resolution_suggestion="This could be dark comedy, which is valid. Clarify if this is intentional.",
                    character_name=None
                ))

        return conflicts

    def _check_cross_setting_conflicts(self, settings: ExtractedSettings) -> List[Conflict]:
        """Check for conflicts between different setting types."""
        conflicts = []

        # Check world type vs style
        if settings.world and settings.world.world_type and settings.style:
            world_type_lower = settings.world.world_type.lower()

            # Fantasy world with contemporary/modern writing style
            if "fantasy" in world_type_lower and settings.style.writing_style:
                style_lower = settings.style.writing_style.lower()
                if "modern" in style_lower or "contemporary" in style_lower:
                    conflicts.append(Conflict(
                        conflict_type="world_style_conflict",
                        setting_type=SettingType.STYLE,
                        field_name="writing_style",
                        original_value="fantasy world",
                        new_value=settings.style.writing_style,
                        severity=ConflictSeverity.LOW,
                        description="Fantasy world with modern writing style",
                        resolution_suggestion="Consider if a more traditional or formal writing style would fit the fantasy setting better, or if modern style is intentional.",
                        character_name=None
                    ))

        # Check character vs world consistency
        if settings.world and settings.world.world_type:
            world_type_lower = settings.world.world_type.lower()
            for character in settings.characters:
                if character.abilities and character.abilities:
                    abilities_str = " ".join(character.abilities).lower()

                    # Magic abilities in non-fantasy world
                    if any(magic in abilities_str for magic in ["magic", "spell", "mana", "法术", "魔法"]):
                        if "fantasy" not in world_type_lower:
                            conflicts.append(Conflict(
                                conflict_type="character_world_conflict",
                                setting_type=SettingType.CHARACTER,
                                field_name="abilities",
                                original_value=settings.world.world_type,
                                new_value="magic abilities",
                                severity=ConflictSeverity.MEDIUM,
                                description=f"Character {character.name or ''} has magic abilities in a non-fantasy world",
                                resolution_suggestion=f"Either change the world type to fantasy, or remove magic abilities from {character.name or 'the character'}.",
                                character_name=character.name
                            ))

        return conflicts

    def has_high_severity_conflicts(self, settings: ExtractedSettings) -> bool:
        """
        Quick check if settings have any high-severity conflicts.

        Args:
            settings: Extracted settings to check

        Returns:
            True if high severity conflicts exist, False otherwise
        """
        conflicts = self.detect_conflicts(settings)
        return any(c.severity == ConflictSeverity.HIGH for c in conflicts)

    def get_conflicts_by_severity(self,
                                  settings: ExtractedSettings,
                                  severity: ConflictSeverity) -> List[Conflict]:
        """
        Get all conflicts of a specific severity level.

        Args:
            settings: Extracted settings to check
            severity: Severity level to filter by

        Returns:
            List of conflicts with the specified severity
        """
        conflicts = self.detect_conflicts(settings)
        return [c for c in conflicts if c.severity == severity]
