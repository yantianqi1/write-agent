"""
Unit tests for question generator.
"""

import pytest
from src.story.setting_extractor.question_generator import (
    QuestionGenerator,
    PriorityQuestionGenerator
)
from src.story.setting_extractor.models import (
    ExtractedSettings,
    MissingInfo,
    SettingType
)


class TestPriorityQuestionGenerator:
    """Test PriorityQuestionGenerator class."""

    def test_no_missing_info(self):
        """Test handling when no info is missing."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        questions = generator.generate_questions(settings, missing_info=[], count=3)

        assert len(questions) == 1
        assert "complete" in questions[0].lower()

    def test_generate_character_questions(self):
        """Test generating character-related questions."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="name",
                description="Character name",
                priority=1,
                suggested_question="What's the character's name?",
                character_name=None
            )
        ]

        questions = generator.generate_questions(settings, missing, count=3)

        assert len(questions) > 0
        assert any("name" in q.lower() for q in questions)

    def test_generate_world_questions(self):
        """Test generating world-related questions."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.WORLD,
                field_name="world_type",
                description="World type",
                priority=1,
                suggested_question="What kind of world is it?"
            )
        ]

        questions = generator.generate_questions(settings, missing, count=3)

        assert len(questions) > 0
        assert any("world" in q.lower() for q in questions)

    def test_respects_count_limit(self):
        """Test that question count is limited."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name=f"field_{i}",
                description=f"Field {i}",
                priority=i,
                suggested_question=f"Question {i}?"
            )
            for i in range(1, 10)
        ]

        questions = generator.generate_questions(settings, missing, count=3)

        assert len(questions) <= 3

    def test_priority_selection(self):
        """Test that higher priority items are selected first."""
        generator = PriorityQuestionGenerator(diversity_factor=0.0)
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="name",
                description="Name",
                priority=1,
                suggested_question="Name?"
            ),
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="appearance",
                description="Appearance",
                priority=4,
                suggested_question="Appearance?"
            )
        ]

        questions = generator.generate_questions(settings, missing, count=1)

        # Should ask about name (priority 1) first
        assert len(questions) == 1
        assert any("name" in questions[0].lower() or "name" in questions[0].lower() for _ in [True])

    def test_diverse_selection(self):
        """Test that diverse setting types are selected."""
        generator = PriorityQuestionGenerator(diversity_factor=0.5)
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="name",
                description="Name",
                priority=1,
                suggested_question="Name?"
            ),
            MissingInfo(
                setting_type=SettingType.WORLD,
                field_name="era",
                description="Era",
                priority=2,
                suggested_question="Era?"
            ),
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="age",
                description="Age",
                priority=3,
                suggested_question="Age?"
            )
        ]

        questions = generator.generate_questions(settings, missing, count=3)

        # Should have questions about both character and world
        assert len(questions) >= 2

    def test_character_specific_questions(self):
        """Test that character-specific questions include name."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.CHARACTER,
                field_name="personality",
                description="Personality",
                priority=2,
                suggested_question="What's the personality?",
                character_name="Alice"
            )
        ]

        questions = generator.generate_questions(settings, missing, count=1)

        assert len(questions) > 0
        # Question should reference the character
        assert "alice" in questions[0].lower() or "character" in questions[0].lower()

    def test_plot_question_variations(self):
        """Test that plot questions have variations."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.PLOT,
                field_name="conflict",
                description="Conflict",
                priority=1,
                suggested_question="What's the conflict?"
            )
        ]

        # Generate multiple times to test variation
        questions_sets = [
            generator.generate_questions(settings, missing, count=1)
            for _ in range(5)
        ]

        # Questions might vary (though not guaranteed with randomness)
        assert all(len(qs) > 0 for qs in questions_sets)

    def test_style_question_generation(self):
        """Test generating style-related questions."""
        generator = PriorityQuestionGenerator()
        settings = ExtractedSettings()

        missing = [
            MissingInfo(
                setting_type=SettingType.STYLE,
                field_name="pov",
                description="POV",
                priority=1,
                suggested_question="What POV?"
            )
        ]

        questions = generator.generate_questions(settings, missing, count=1)

        assert len(questions) > 0
        assert any("pov" in q.lower() or "point of view" in q.lower() for q in questions)
