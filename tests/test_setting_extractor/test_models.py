"""
Unit tests for data models.
"""

import pytest
from story.setting_extractor.models import (
    UserIntent, SettingType, ConflictSeverity,
    CharacterProfile, WorldSetting, PlotElement, StylePreference,
    ExtractedSettings, MissingInfo, Conflict,
    ExtractionRequest, ExtractionResult
)


class TestCharacterProfile:
    """Test CharacterProfile data class."""

    def test_create_empty_character(self):
        """Test creating an empty character profile."""
        char = CharacterProfile()
        assert char.is_empty()

    def test_create_character_with_data(self):
        """Test creating a character with data."""
        char = CharacterProfile(
            name="Alice",
            personality="Brave and curious",
            age=25,
            role="protagonist"
        )
        assert not char.is_empty()
        assert char.name == "Alice"
        assert char.personality == "Brave and curious"
        assert char.age == 25
        assert char.role == "protagonist"

    def test_character_to_dict(self):
        """Test converting character to dictionary."""
        char = CharacterProfile(
            name="Bob",
            abilities=["fire magic", "sword fighting"],
            relationships=["Alice", "Charlie"]
        )
        char_dict = char.to_dict()

        assert char_dict["name"] == "Bob"
        assert len(char_dict["abilities"]) == 2
        assert "fire magic" in char_dict["abilities"]
        assert len(char_dict["relationships"]) == 2

    def test_character_merge(self):
        """Test merging two character profiles."""
        char1 = CharacterProfile(
            name="Alice",
            personality="Brave",
            abilities=["fire magic"]
        )
        char2 = CharacterProfile(
            name="Alice",
            background="Former knight",
            abilities=["healing"]
        )

        merged = char1.merge(char2)

        assert merged.name == "Alice"
        assert merged.personality == "Brave"
        assert merged.background == "Former knight"
        assert len(merged.abilities) == 2
        assert "fire magic" in merged.abilities
        assert "healing" in merged.abilities

    def test_character_merge_new_values_override(self):
        """Test that new values override old ones in merge."""
        char1 = CharacterProfile(name="Alice", age=25)
        char2 = CharacterProfile(name="Alice", age=30)

        merged = char1.merge(char2)
        assert merged.age == 30  # New value overrides


class TestWorldSetting:
    """Test WorldSetting data class."""

    def test_create_empty_world(self):
        """Test creating an empty world setting."""
        world = WorldSetting()
        assert world.is_empty()

    def test_world_with_data(self):
        """Test creating a world with data."""
        world = WorldSetting(
            world_type="fantasy",
            era="medieval",
            magic_system="elemental magic"
        )
        assert not world.is_empty()
        assert world.world_type == "fantasy"

    def test_world_to_dict(self):
        """Test converting world to dictionary."""
        world = WorldSetting(
            locations=["Castle", "Forest"],
            factions=["Knights", "Mages"]
        )
        world_dict = world.to_dict()

        assert len(world_dict["locations"]) == 2
        assert len(world_dict["factions"]) == 2

    def test_world_merge(self):
        """Test merging two world settings."""
        world1 = WorldSetting(
            world_type="fantasy",
            locations=["Castle"]
        )
        world2 = WorldSetting(
            era="medieval",
            locations=["Forest", "Mountain"]
        )

        merged = world1.merge(world2)

        assert merged.world_type == "fantasy"
        assert merged.era == "medieval"
        assert len(merged.locations) == 3


class TestPlotElement:
    """Test PlotElement data class."""

    def test_create_empty_plot(self):
        """Test creating an empty plot element."""
        plot = PlotElement()
        assert plot.is_empty()

    def test_plot_with_data(self):
        """Test creating a plot with data."""
        plot = PlotElement(
            conflict="Good vs Evil",
            themes=["redemption", "sacrifice"]
        )
        assert not plot.is_empty()
        assert plot.conflict == "Good vs Evil"

    def test_plot_merge(self):
        """Test merging two plot elements."""
        plot1 = PlotElement(
            conflict="War",
            themes=["survival"]
        )
        plot2 = PlotElement(
            rising_action=["Battle 1", "Battle 2"],
            themes=["honor"]
        )

        merged = plot1.merge(plot2)

        assert merged.conflict == "War"
        assert len(merged.themes) == 2
        assert len(merged.rising_action) == 2


class TestStylePreference:
    """Test StylePreference data class."""

    def test_create_empty_style(self):
        """Test creating an empty style preference."""
        style = StylePreference()
        assert style.is_empty()

    def test_style_with_data(self):
        """Test creating a style with data."""
        style = StylePreference(
            pov="first person",
            tone="serious"
        )
        assert not style.is_empty()
        assert style.pov == "first person"

    def test_style_merge(self):
        """Test merging two style preferences."""
        style1 = StylePreference(
            pov="first person",
            genre=["fantasy"]
        )
        style2 = StylePreference(
            tone="dark",
            genre=["adventure"]
        )

        merged = style1.merge(style2)

        assert merged.pov == "first person"
        assert merged.tone == "dark"
        assert len(merged.genre) == 2


class TestExtractedSettings:
    """Test ExtractedSettings container."""

    def test_create_empty_settings(self):
        """Test creating empty extracted settings."""
        settings = ExtractedSettings()
        assert settings.is_empty()

    def test_settings_with_characters(self):
        """Test settings with character data."""
        settings = ExtractedSettings(
            characters=[CharacterProfile(name="Alice")]
        )
        assert not settings.is_empty()

    def test_merge_character_by_name(self):
        """Test that merging combines characters with same name."""
        settings1 = ExtractedSettings(
            characters=[
                CharacterProfile(name="Alice", personality="Brave")
            ]
        )
        settings2 = ExtractedSettings(
            characters=[
                CharacterProfile(name="Alice", age=25),
                CharacterProfile(name="Bob")
            ]
        )

        merged = settings1.merge(settings2)

        assert len(merged.characters) == 2
        alice = next(c for c in merged.characters if c.name == "Alice")
        assert alice.personality == "Brave"
        assert alice.age == 25

    def test_merge_world_settings(self):
        """Test merging world settings."""
        settings1 = ExtractedSettings(
            world=WorldSetting(world_type="fantasy")
        )
        settings2 = ExtractedSettings(
            world=WorldSetting(era="medieval")
        )

        merged = settings1.merge(settings2)

        assert merged.world.world_type == "fantasy"
        assert merged.world.era == "medieval"


class TestMissingInfo:
    """Test MissingInfo data class."""

    def test_create_missing_info(self):
        """Test creating missing info."""
        missing = MissingInfo(
            setting_type=SettingType.CHARACTER,
            field_name="age",
            description="Character age",
            priority=2,
            suggested_question="How old is the character?"
        )

        assert missing.setting_type == SettingType.CHARACTER
        assert missing.priority == 2

    def test_missing_info_to_dict(self):
        """Test converting missing info to dictionary."""
        missing = MissingInfo(
            setting_type=SettingType.WORLD,
            field_name="era",
            description="Time period",
            priority=1,
            suggested_question="When is it set?",
            character_name=None
        )

        missing_dict = missing.to_dict()

        assert missing_dict["setting_type"] == "world"
        assert missing_dict["priority"] == 1


class TestConflict:
    """Test Conflict data class."""

    def test_create_conflict(self):
        """Test creating a conflict."""
        conflict = Conflict(
            conflict_type="world_type_conflict",
            setting_type=SettingType.WORLD,
            field_name="world_type",
            original_value="fantasy",
            new_value="sci-fi",
            severity=ConflictSeverity.HIGH,
            description="Cannot be both fantasy and sci-fi",
            resolution_suggestion="Choose one"
        )

        assert conflict.severity == ConflictSeverity.HIGH
        assert conflict.setting_type == SettingType.WORLD

    def test_conflict_to_dict(self):
        """Test converting conflict to dictionary."""
        conflict = Conflict(
            conflict_type="personality_conflict",
            setting_type=SettingType.CHARACTER,
            field_name="personality",
            original_value="shy",
            new_value="outgoing",
            severity=ConflictSeverity.MEDIUM,
            description="Contradictory traits",
            resolution_suggestion="Clarify",
            character_name="Alice"
        )

        conflict_dict = conflict.to_dict()

        assert conflict_dict["severity"] == "medium"
        assert conflict_dict["character_name"] == "Alice"


class TestExtractionRequest:
    """Test ExtractionRequest data class."""

    def test_create_request(self):
        """Test creating an extraction request."""
        request = ExtractionRequest(
            user_input="Create a character named Alice",
            incremental_mode=True
        )

        assert request.user_input == "Create a character named Alice"
        assert request.incremental_mode is True
        assert request.existing_settings is None

    def test_request_with_existing_settings(self):
        """Test request with existing settings."""
        existing = ExtractedSettings(
            characters=[CharacterProfile(name="Bob")]
        )
        request = ExtractionRequest(
            user_input="Add another character",
            existing_settings=existing,
            incremental_mode=True
        )

        assert request.existing_settings is not None
        assert len(request.existing_settings.characters) == 1


class TestExtractionResult:
    """Test ExtractionResult data class."""

    def test_create_result(self):
        """Test creating an extraction result."""
        settings = ExtractedSettings(
            characters=[CharacterProfile(name="Alice")]
        )

        result = ExtractionResult(
            extracted_settings=settings,
            detected_intent=UserIntent.CREATE,
            involved_types=[SettingType.CHARACTER],
            missing_info=[],
            conflicts=[],
            suggested_questions=[],
            confidence=0.8
        )

        assert result.detected_intent == UserIntent.CREATE
        assert result.confidence == 0.8
        assert len(result.involved_types) == 1

    def test_has_critical_issues(self):
        """Test checking for critical issues."""
        settings = ExtractedSettings()

        # No conflicts
        result1 = ExtractionResult(
            extracted_settings=settings,
            detected_intent=UserIntent.CREATE,
            involved_types=[],
            missing_info=[],
            conflicts=[],
            suggested_questions=[],
            confidence=0.8
        )
        assert not result1.has_critical_issues()

        # Has high severity conflict
        conflict = Conflict(
            conflict_type="test",
            setting_type=SettingType.WORLD,
            field_name="test",
            original_value="a",
            new_value="b",
            severity=ConflictSeverity.HIGH,
            description="test",
            resolution_suggestion="fix it"
        )
        result2 = ExtractionResult(
            extracted_settings=settings,
            detected_intent=UserIntent.CREATE,
            involved_types=[],
            missing_info=[],
            conflicts=[conflict],
            suggested_questions=[],
            confidence=0.8
        )
        assert result2.has_critical_issues()

    def test_get_missing_by_priority(self):
        """Test filtering missing info by priority."""
        settings = ExtractedSettings()

        missing1 = MissingInfo(
            setting_type=SettingType.CHARACTER,
            field_name="name",
            description="Name",
            priority=1,
            suggested_question="What's the name?"
        )
        missing2 = MissingInfo(
            setting_type=SettingType.CHARACTER,
            field_name="age",
            description="Age",
            priority=3,
            suggested_question="What's the age?"
        )

        result = ExtractionResult(
            extracted_settings=settings,
            detected_intent=UserIntent.CREATE,
            involved_types=[],
            missing_info=[missing1, missing2],
            conflicts=[],
            suggested_questions=[],
            confidence=0.8
        )

        # Get only priority 1 and 2
        high_priority = result.get_missing_by_priority(max_priority=2)
        assert len(high_priority) == 1
        assert high_priority[0].field_name == "name"
