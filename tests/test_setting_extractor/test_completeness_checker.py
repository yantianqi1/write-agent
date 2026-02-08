"""
Unit tests for completeness checker.
"""

import pytest
from story.setting_extractor.completeness_checker import (
    CompletenessChecker,
    BasicCompletenessChecker
)
from story.setting_extractor.models import (
    ExtractedSettings,
    CharacterProfile,
    WorldSetting,
    PlotElement,
    StylePreference,
    SettingType,
    MissingInfo
)


class TestBasicCompletenessChecker:
    """Test BasicCompletenessChecker class."""

    def test_empty_settings_have_missing_info(self):
        """Test that empty settings generate missing info."""
        checker = BasicCompletenessChecker()
        settings = ExtractedSettings()

        missing = checker.check_completeness(settings)

        assert len(missing) > 0

    def test_complete_character_no_missing(self):
        """Test that complete character has no missing info."""
        checker = BasicCompletenessChecker()

        character = CharacterProfile(
            name="Alice",
            role="protagonist",
            personality="Brave and kind",
            background="Former knight",
            appearance="Tall with red hair",
            age=25,
            abilities=["sword fighting"],
            relationships=["Bob"]
        )

        settings = ExtractedSettings(
            characters=[character],
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="Good vs evil"),
            style=StylePreference(pov="first person")
        )

        missing = checker.check_completeness(settings)

        # Should have minimal missing info for this character
        char_missing = [m for m in missing if m.character_name == "Alice"]
        assert len(char_missing) == 0

    def test_missing_character_name(self):
        """Test detecting missing character name."""
        checker = BasicCompletenessChecker()

        character = CharacterProfile(role="protagonist")
        settings = ExtractedSettings(
            characters=[character],
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="test"),
            style=StylePreference(pov="first")
        )

        missing = checker.check_completeness(settings)

        name_missing = [m for m in missing if m.field_name == "name"]
        assert len(name_missing) > 0
        assert name_missing[0].priority == 1

    def test_missing_world_type(self):
        """Test detecting missing world type."""
        checker = BasicCompletenessChecker()

        settings = ExtractedSettings(
            characters=[CharacterProfile(name="Alice", role="protagonist")],
            plot=PlotElement(conflict="test"),
            style=StylePreference(pov="first")
        )

        missing = checker.check_completeness(settings)

        world_missing = [m for m in missing if m.setting_type == SettingType.WORLD]
        assert len(world_missing) > 0

    def test_priority_ordering(self):
        """Test that missing info is sorted by priority."""
        checker = BasicCompletenessChecker()

        settings = ExtractedSettings()

        missing = checker.check_completeness(settings)

        # Check that list is sorted by priority (ascending)
        priorities = [m.priority for m in missing]
        assert priorities == sorted(priorities)

    def test_completeness_score(self):
        """Test calculating completeness score."""
        checker = BasicCompletenessChecker()

        # Empty settings
        empty_settings = ExtractedSettings()
        score_empty = checker.get_completeness_score(empty_settings)
        assert score_empty < 0.5

        # More complete settings
        complete_settings = ExtractedSettings(
            characters=[CharacterProfile(
                name="Alice",
                role="protagonist",
                personality="Brave",
                background="Knight",
                appearance="Tall",
                age=25
            )],
            world=WorldSetting(
                world_type="fantasy",
                era="medieval",
                magic_system="elemental"
            ),
            plot=PlotElement(
                conflict="war",
                climax="battle",
                resolution="peace"
            ),
            style=StylePreference(
                pov="first person",
                writing_style="casual",
                tone="serious"
            )
        )
        score_complete = checker.get_completeness_score(complete_settings)
        assert score_complete > score_empty

    def test_is_minimally_complete_true(self):
        """Test checking if settings are minimally complete."""
        checker = BasicCompletenessChecker()

        settings = ExtractedSettings(
            characters=[CharacterProfile(name="Alice", role="protagonist")],
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="war"),
            style=StylePreference(pov="first person")
        )

        assert checker.is_minimally_complete(settings) is True

    def test_is_minimally_complete_false(self):
        """Test checking if settings are not minimally complete."""
        checker = BasicCompletenessChecker()

        # Missing POV
        settings = ExtractedSettings(
            characters=[CharacterProfile(name="Alice", role="protagonist")],
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="war")
            # No style
        )

        assert checker.is_minimally_complete(settings) is False

    def test_check_all_characters(self):
        """Test checking completeness for all characters."""
        checker = BasicCompletenessChecker(require_all_characters=True)

        settings = ExtractedSettings(
            characters=[
                CharacterProfile(name="Alice", role="protagonist"),
                CharacterProfile(role="antagonist")  # Missing name
            ],
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="test"),
            style=StylePreference(pov="first")
        )

        missing = checker.check_completeness(settings)

        # Should have missing info for the second character
        antagonist_missing = [m for m in missing if m.field_name == "name"]
        assert len(antagonist_missing) >= 1

    def test_suggested_questions_generated(self):
        """Test that suggested questions are generated."""
        checker = BasicCompletenessChecker()

        settings = ExtractedSettings(
            characters=[CharacterProfile(role="protagonist")],  # Missing name
            world=WorldSetting(world_type="fantasy", era="medieval"),
            plot=PlotElement(conflict="test"),
            style=StylePreference(pov="first")
        )

        missing = checker.check_completeness(settings)

        # At least one missing info should have a suggested question
        assert all(m.suggested_question for m in missing)
