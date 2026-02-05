"""
Modification understanding and application engine.

This module understands natural language modification instructions
and applies them to story settings while maintaining consistency.

Users say things like "make the protagonist braver" or "change the
ending to be more hopeful" and this engine figures out what to change.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import re

from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType, UserIntent
)


class ModificationScope(Enum):
    """Scope of modification."""
    CHARACTER = "character"  # Modify a character
    WORLD = "world"  # Modify world setting
    PLOT = "plot"  # Modify plot element
    STYLE = "style"  # Modify style preference
    CONTENT = "content"  # Modify actual story content (future)


class ModificationType(Enum):
    """Type of modification operation."""
    UPDATE = "update"  # Update a field value
    ADD = "add"  # Add new information
    REMOVE = "remove"  # Remove information
    REPLACE = "replace"  # Replace entirely
    ADJUST = "adjust"  # Make a qualitative adjustment (e.g., "more brave")


@dataclass
class ModificationTarget:
    """Target of a modification instruction."""
    scope: ModificationScope
    target_name: Optional[str] = None  # e.g., character name
    field_name: Optional[str] = None  # e.g., "personality"
    target_id: Optional[str] = None  # For content: chapter/paragraph ID


@dataclass
class ModificationInstruction:
    """Parsed modification instruction."""
    scope: ModificationScope
    mod_type: ModificationType
    target: ModificationTarget
    new_value: Optional[str] = None
    adjustment_delta: Optional[str] = None  # For ADJUST type (e.g., "more", "less")
    confidence: float = 0.0
    raw_input: str = ""


@dataclass
class ModificationResult:
    """Result of applying a modification."""
    success: bool
    modified_settings: ExtractedSettings
    changes_description: List[str]
    confidence: float
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "modified_settings": self.modified_settings.to_dict(),
            "changes_description": self.changes_description,
            "confidence": self.confidence,
            "warnings": self.warnings
        }


class ModificationParser(ABC):
    """Abstract base class for modification parsers."""

    @abstractmethod
    def parse(self, user_input: str,
             current_settings: ExtractedSettings) -> ModificationInstruction:
        """Parse user input into a modification instruction."""
        pass


class RuleBasedModificationParser(ModificationParser):
    """
    Rule-based parser for modification instructions.

    This parser uses pattern matching to understand what
    the user wants to modify.
    """

    # Character modification patterns
    CHARACTER_PATTERNS = {
        # "让X更勇敢" -> make X more brave
        "more_adj": re.compile(
            r'(?:让|make|使)(.+?)(?:更|more|更)(.+?)(?:一点|些|些|\.|$)',
            re.IGNORECASE
        ),
        # "X的性格是..." -> X's personality is...
        "set_personality": re.compile(
            r'(.+?)(?:的|s?)(?:性格|个性|personality)(?:是|:|is)\s*(.+?)(?:，|。|\.|$)',
            re.IGNORECASE
        ),
        # "主角叫..." -> protagonist is named...
        "set_name": re.compile(
            r'(?:主角|character|他|她)(?:叫|is|名字为|named?)\s*([^\s，。\.]{1,10})',
            re.IGNORECASE
        ),
    }

    # Qualitative mappings for adjustments
    ADJECTIVE_MAPPING = {
        "勇敢": ("personality", "勇敢，果断"),
        "果断": ("personality", "果断，坚定"),
        "软弱": ("personality", "软弱，犹豫"),
        "聪明": ("personality", "聪明，机智"),
        "善良": ("personality", "善良，乐于助人"),
        "邪恶": ("personality", "邪恶，自私"),
        "幽默": ("personality", "幽默，风趣"),
        "严肃": ("personality", "严肃，认真"),
    }

    def __init__(self):
        """Initialize the parser."""
        self._init_plot_patterns()
        self._init_style_patterns()
        self._init_world_patterns()

    def _init_plot_patterns(self):
        """Initialize plot modification patterns."""
        self.plot_patterns = {
            "change_conflict": re.compile(
                r'(?:冲突|conflict)(?:改为|变更为|:)\s*(.+)',
                re.IGNORECASE
            ),
            "change_ending": re.compile(
                r'(?:结局|ending|结尾)(?:改成|改为|:)\s*(.+)',
                re.IGNORECASE
            ),
        }

    def _init_style_patterns(self):
        """Initialize style modification patterns."""
        self.style_patterns = {
            "more_humorous": re.compile(
                r'(?:写得更|more|更)(?:幽默|搞笑|funny|humorous)',
                re.IGNORECASE
            ),
            "more_serious": re.compile(
                r'(?:写得更|more|更)(?:严肃|serious|dark)',
                re.IGNORECASE
            ),
        }

    def _init_world_patterns(self):
        """Initialize world modification patterns."""
        self.world_patterns = {
            "change_magic": re.compile(
                r'(?:魔法|magic)(?:系统|system)?(?:改为|:)\s*(.+)',
                re.IGNORECASE
            ),
        }

    def parse(self, user_input: str,
             current_settings: ExtractedSettings) -> ModificationInstruction:
        """
        Parse user input into a modification instruction.

        Args:
            user_input: User's natural language modification request
            current_settings: Current settings for context

        Returns:
            Parsed ModificationInstruction
        """
        input_lower = user_input.lower()

        # Try character modifications first
        char_mod = self._parse_character_modification(user_input, current_settings)
        if char_mod:
            return char_mod

        # Try plot modifications
        plot_mod = self._parse_plot_modification(user_input, current_settings)
        if plot_mod:
            return plot_mod

        # Try style modifications
        style_mod = self._parse_style_modification(user_input, current_settings)
        if style_mod:
            return style_mod

        # Try world modifications
        world_mod = self._parse_world_modification(user_input, current_settings)
        if world_mod:
            return world_mod

        # Default: treat as general update
        return ModificationInstruction(
            scope=ModificationScope.CHARACTER,
            mod_type=ModificationType.UPDATE,
            target=ModificationTarget(scope=ModificationScope.CHARACTER, field_name="general"),
            new_value=user_input,
            confidence=0.3,
            raw_input=user_input
        )

    def _parse_character_modification(self, user_input: str,
                                     settings: ExtractedSettings) -> Optional[ModificationInstruction]:
        """Parse character-specific modifications."""
        # Try "让X更adj" pattern
        match = self.CHARACTER_PATTERNS["more_adj"].search(user_input)
        if match:
            char_name = match.group(1).strip()
            adjective = match.group(2).strip()

            # Map adjective to field and value
            field_name, suggested_value = self.ADJECTIVE_MAPPING.get(
                adjective, ("personality", f"更{adjective}")
            )

            # Find target character
            target_name = self._find_character(char_name, settings)

            return ModificationInstruction(
                scope=ModificationScope.CHARACTER,
                mod_type=ModificationType.ADJUST,
                target=ModificationTarget(
                    scope=ModificationScope.CHARACTER,
                    target_name=target_name,
                    field_name=field_name
                ),
                new_value=suggested_value,
                adjustment_delta=adjective,
                confidence=0.8,
                raw_input=user_input
            )

        # Try personality set pattern
        match = self.CHARACTER_PATTERNS["set_personality"].search(user_input)
        if match:
            char_name = match.group(1).strip()
            personality = match.group(2).strip()

            target_name = self._find_character(char_name, settings)

            return ModificationInstruction(
                scope=ModificationScope.CHARACTER,
                mod_type=ModificationType.UPDATE,
                target=ModificationTarget(
                    scope=ModificationScope.CHARACTER,
                    target_name=target_name,
                    field_name="personality"
                ),
                new_value=personality,
                confidence=0.85,
                raw_input=user_input
            )

        return None

    def _parse_plot_modification(self, user_input: str,
                                settings: ExtractedSettings) -> Optional[ModificationInstruction]:
        """Parse plot-specific modifications."""
        # Try conflict change
        match = self.plot_patterns["change_conflict"].search(user_input)
        if match:
            new_conflict = match.group(1).strip()
            return ModificationInstruction(
                scope=ModificationScope.PLOT,
                mod_type=ModificationType.UPDATE,
                target=ModificationTarget(
                    scope=ModificationScope.PLOT,
                    field_name="conflict"
                ),
                new_value=new_conflict,
                confidence=0.8,
                raw_input=user_input
            )

        # Try ending change
        match = self.plot_patterns["change_ending"].search(user_input)
        if match:
            new_ending = match.group(1).strip()
            return ModificationInstruction(
                scope=ModificationScope.PLOT,
                mod_type=ModificationType.UPDATE,
                target=ModificationTarget(
                    scope=ModificationScope.PLOT,
                    field_name="resolution"
                ),
                new_value=new_ending,
                confidence=0.8,
                raw_input=user_input
            )

        return None

    def _parse_style_modification(self, user_input: str,
                                 settings: ExtractedSettings) -> Optional[ModificationInstruction]:
        """Parse style-specific modifications."""
        # Try more humorous
        match = self.style_patterns["more_humorous"].search(user_input)
        if match:
            return ModificationInstruction(
                scope=ModificationScope.STYLE,
                mod_type=ModificationType.ADJUST,
                target=ModificationTarget(
                    scope=ModificationScope.STYLE,
                    field_name="tone"
                ),
                new_value="幽默",
                adjustment_delta="more",
                confidence=0.9,
                raw_input=user_input
            )

        # Try more serious
        match = self.style_patterns["more_serious"].search(user_input)
        if match:
            return ModificationInstruction(
                scope=ModificationScope.STYLE,
                mod_type=ModificationType.ADJUST,
                target=ModificationTarget(
                    scope=ModificationScope.STYLE,
                    field_name="tone"
                ),
                new_value="严肃",
                adjustment_delta="more",
                confidence=0.9,
                raw_input=user_input
            )

        return None

    def _parse_world_modification(self, user_input: str,
                                  settings: ExtractedSettings) -> Optional[ModificationInstruction]:
        """Parse world-specific modifications."""
        match = self.world_patterns["change_magic"].search(user_input)
        if match:
            new_magic = match.group(1).strip()
            return ModificationInstruction(
                scope=ModificationScope.WORLD,
                mod_type=ModificationType.UPDATE,
                target=ModificationTarget(
                    scope=ModificationScope.WORLD,
                    field_name="magic_system"
                ),
                new_value=new_magic,
                confidence=0.8,
                raw_input=user_input
            )

        return None

    def _find_character(self, name_or_role: str,
                       settings: ExtractedSettings) -> Optional[str]:
        """Find a character by name or role."""
        # Try exact name match
        for char in settings.characters:
            if char.name and char.name in name_or_role:
                return char.name

        # Try role match
        for char in settings.characters:
            if char.role and char.role in name_or_role:
                return char.name or f"character_{id(char)}"

        # Try pronouns - assume first character or protagonist
        if any(p in name_or_role for p in ["他", "她", "主角", "主角", "the character"]):
            for char in settings.characters:
                if char.role == "主角":
                    return char.name or "主角"
            if settings.characters:
                return settings.characters[0].name or "主角"

        return name_or_role


class ModificationEngine:
    """
    Main engine for understanding and applying modifications.

    This engine:
    1. Parses natural language modification instructions
    2. Locates the target of modification
    3. Applies the modification
    4. Maintains consistency across related settings
    """

    def __init__(self):
        """Initialize the modification engine."""
        self.parser = RuleBasedModificationParser()

    def process(self, user_input: str,
               current_settings: ExtractedSettings) -> ModificationResult:
        """
        Process a modification request.

        Args:
            user_input: User's natural language modification request
            current_settings: Current story settings

        Returns:
            ModificationResult with updated settings and change description
        """
        # Step 1: Parse the instruction
        instruction = self.parser.parse(user_input, current_settings)

        # Step 2: Apply the modification
        modified_settings, changes = self._apply_instruction(
            instruction, current_settings
        )

        # Step 3: Check for consistency issues
        warnings = self._check_consistency(instruction, current_settings, modified_settings)

        return ModificationResult(
            success=True,
            modified_settings=modified_settings,
            changes_description=changes,
            confidence=instruction.confidence,
            warnings=warnings
        )

    def _apply_instruction(self, instruction: ModificationInstruction,
                          settings: ExtractedSettings) -> Tuple[ExtractedSettings, List[str]]:
        """Apply a modification instruction to settings."""
        changes = []

        if instruction.scope == ModificationScope.CHARACTER:
            return self._apply_character_mod(instruction, settings)
        elif instruction.scope == ModificationScope.PLOT:
            return self._apply_plot_mod(instruction, settings)
        elif instruction.scope == ModificationScope.STYLE:
            return self._apply_style_mod(instruction, settings)
        elif instruction.scope == ModificationScope.WORLD:
            return self._apply_world_mod(instruction, settings)

        return settings, []

    def _apply_character_mod(self, instruction: ModificationInstruction,
                            settings: ExtractedSettings) -> Tuple[ExtractedSettings, List[str]]:
        """Apply a character modification."""
        changes = []
        modified_chars = []

        # Find target character
        target_char = None
        target_index = -1

        for i, char in enumerate(settings.characters):
            if (instruction.target.target_name and
                char.name == instruction.target.target_name):
                target_char = char
                target_index = i
                break
            if char.role == instruction.target.target_name:
                target_char = char
                target_index = i
                break

        # If not found, use first character
        if target_char is None and settings.characters:
            target_char = settings.characters[0]
            target_index = 0

        # Create modified character
        if target_char:
            if instruction.target.field_name == "personality":
                old_personality = target_char.personality or ""
                new_personality = instruction.new_value

                if instruction.mod_type == ModificationType.ADJUST:
                    # For "more adj", combine with existing
                    if old_personality:
                        new_personality = f"{old_personality}，{new_personality}"

                modified_char = CharacterProfile(
                    name=target_char.name,
                    personality=new_personality,
                    background=target_char.background,
                    relationships=target_char.relationships,
                    abilities=target_char.abilities,
                    appearance=target_char.appearance,
                    age=target_char.age,
                    role=target_char.role
                )
                changes.append(f"更新角色{target_char.name or ''}的性格: {old_personality} → {new_personality}")
            else:
                # Generic field update
                modified_char = target_char
                setattr(modified_char, instruction.target.field_name, instruction.new_value)
                changes.append(f"更新角色{target_char.name or ''}的{instruction.target.field_name}")

            # Replace in list
            modified_chars = settings.characters.copy()
            if target_index >= 0:
                modified_chars[target_index] = modified_char
            else:
                modified_chars.append(modified_char)
        else:
            # Create new character
            modified_char = CharacterProfile(
                name=instruction.target.target_name,
                **{instruction.target.field_name: instruction.new_value}
            )
            modified_chars = settings.characters + [modified_char]
            changes.append(f"添加新角色: {instruction.target.target_name}")

        return (
            ExtractedSettings(
                characters=modified_chars,
                world=settings.world,
                plot=settings.plot,
                style=settings.style
            ),
            changes
        )

    def _apply_plot_mod(self, instruction: ModificationInstruction,
                       settings: ExtractedSettings) -> Tuple[ExtractedSettings, List[str]]:
        """Apply a plot modification."""
        changes = []
        plot = settings.plot if settings.plot else PlotElement()

        # Update the field
        old_value = getattr(plot, instruction.target.field_name, None)
        setattr(plot, instruction.target.field_name, instruction.new_value)
        changes.append(f"更新情节{instruction.target.field_name}: {old_value} → {instruction.new_value}")

        return (
            ExtractedSettings(
                characters=settings.characters,
                world=settings.world,
                plot=plot,
                style=settings.style
            ),
            changes
        )

    def _apply_style_mod(self, instruction: ModificationInstruction,
                        settings: ExtractedSettings) -> Tuple[ExtractedSettings, List[str]]:
        """Apply a style modification."""
        changes = []
        style = settings.style if settings.style else StylePreference()

        # Update the field
        old_value = getattr(style, instruction.target.field_name, None)
        setattr(style, instruction.target.field_name, instruction.new_value)
        changes.append(f"更新风格{instruction.target.field_name}: {old_value} → {instruction.new_value}")

        return (
            ExtractedSettings(
                characters=settings.characters,
                world=settings.world,
                plot=settings.plot,
                style=style
            ),
            changes
        )

    def _apply_world_mod(self, instruction: ModificationInstruction,
                        settings: ExtractedSettings) -> Tuple[ExtractedSettings, List[str]]:
        """Apply a world modification."""
        changes = []
        world = settings.world if settings.world else WorldSetting()

        # Update the field
        old_value = getattr(world, instruction.target.field_name, None)
        setattr(world, instruction.target.field_name, instruction.new_value)
        changes.append(f"更新世界观{instruction.target.field_name}: {old_value} → {instruction.new_value}")

        return (
            ExtractedSettings(
                characters=settings.characters,
                world=settings.world,
                plot=settings.plot,
                style=settings.style
            ),
            changes
        )

    def _check_consistency(self, instruction: ModificationInstruction,
                          original: ExtractedSettings,
                          modified: ExtractedSettings) -> List[str]:
        """Check for consistency issues after modification."""
        warnings = []

        # Check if character personality matches world type
        if instruction.scope == ModificationScope.CHARACTER and instruction.target.field_name == "personality":
            if modified.world and modified.world.world_type:
                if "古代" in modified.world.world_type and "现代" in instruction.new_value:
                    warnings.append("角色性格设定与世界观时代不符")

        # Check if plot conflict matches character abilities
        if instruction.scope == ModificationScope.PLOT and instruction.target.field_name == "conflict":
            # Future: validate against character abilities
            pass

        return warnings


def create_modification_engine() -> ModificationEngine:
    """Factory function to create a modification engine."""
    return ModificationEngine()
