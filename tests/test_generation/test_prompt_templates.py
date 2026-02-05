"""
Unit tests for prompt template system.

Tests the StoryTemplateEngine, CompactTemplateEngine, and
related prompt generation functionality.
"""

import sys
import unittest
sys.path.insert(0, '/root/write-agent')

from src.story.generation.prompt_templates import (
    GenerationMode,
    ContentType,
    GenerationContext,
    PromptTemplate,
    TemplateEngine,
    StoryTemplateEngine,
    CompactTemplateEngine,
    create_template_engine
)
from src.story.setting_extractor.models import (
    ExtractedSettings,
    CharacterProfile,
    WorldSetting,
    PlotElement,
    StylePreference
)


class TestGenerationMode(unittest.TestCase):
    """Test GenerationMode enum."""

    def test_modes(self):
        """Test all generation modes exist."""
        modes = [
            GenerationMode.FULL,
            GenerationMode.CONTINUE,
            GenerationMode.EXPAND,
            GenerationMode.REWRITE,
            GenerationMode.OUTLINE
        ]
        for mode in modes:
            self.assertIsNotNone(mode)
            self.assertIsInstance(mode.value, str)


class TestContentType(unittest.TestCase):
    """Test ContentType enum."""

    def test_types(self):
        """Test all content types exist."""
        types = [
            ContentType.CHAPTER,
            ContentType.SCENE,
            ContentType.DIALOGUE,
            ContentType.DESCRIPTION,
            ContentType.ACTION
        ]
        for ct in types:
            self.assertIsNotNone(ct)
            self.assertIsInstance(ct.value, str)


class TestPromptTemplate(unittest.TestCase):
    """Test PromptTemplate dataclass."""

    def test_format(self):
        """Test template formatting."""
        template = PromptTemplate(
            system_prompt="You are a {role}.",
            user_template="Write about {topic}."
        )

        system, user = template.format(role="writer", topic="cats")

        self.assertEqual(system, "You are a writer.")
        self.assertEqual(user, "Write about cats.")


class TestGenerationContext(unittest.TestCase):
    """Test GenerationContext dataclass."""

    def test_default_context(self):
        """Test context with defaults."""
        settings = ExtractedSettings()
        context = GenerationContext(settings=settings)

        self.assertEqual(context.chapter_number, 1)
        self.assertEqual(context.target_word_count, 2000)
        self.assertEqual(context.generation_mode, GenerationMode.FULL)

    def test_full_context(self):
        """Test context with all fields."""
        settings = ExtractedSettings()
        context = GenerationContext(
            settings=settings,
            chapter_number=5,
            target_word_count=3000,
            generation_mode=GenerationMode.CONTINUE,
            previous_content="Previous text...",
            characters_in_scene=["Alice", "Bob"],
            location="Forest",
            mood="Tense"
        )

        self.assertEqual(context.chapter_number, 5)
        self.assertEqual(context.target_word_count, 3000)
        self.assertEqual(context.generation_mode, GenerationMode.CONTINUE)
        self.assertEqual(context.characters_in_scene, ["Alice", "Bob"])
        self.assertEqual(context.location, "Forest")
        self.assertEqual(context.mood, "Tense")


class TestStoryTemplateEngine(unittest.TestCase):
    """Test StoryTemplateEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = StoryTemplateEngine()
        self.settings = ExtractedSettings(
            characters=[
                CharacterProfile(
                    name="张三",
                    role="主角",
                    personality="勇敢、善良",
                    background="一个普通人",
                    appearance="中等身材"
                )
            ],
            world=WorldSetting(
                world_type="武侠世界",
                era="古代",
                magic_system="内功、轻功"
            ),
            plot=PlotElement(
                conflict="张三需要为父母报仇",
                inciting_incident="张三发现仇人线索"
            ),
            style=StylePreference(
                pov="第三人称有限视角",
                tense="过去时",
                tone="紧张",
                pacing="快"
            )
        )

    def test_initialization(self):
        """Test engine initialization."""
        self.assertIsNotNone(self.engine.templates)
        self.assertIn(GenerationMode.FULL, self.engine.templates)
        self.assertIn(GenerationMode.CONTINUE, self.engine.templates)
        self.assertIn(GenerationMode.REWRITE, self.engine.templates)

    def test_generate_full_prompt(self):
        """Test generating prompt for full chapter."""
        context = GenerationContext(
            settings=self.settings,
            chapter_number=1,
            generation_mode=GenerationMode.FULL,
            target_word_count=2000
        )

        system, user = self.engine.generate_prompt(context)

        self.assertIn("作家", system)
        self.assertIn("张三", user)
        self.assertIn("武侠世界", user)
        self.assertIn("2000", system)

    def test_generate_continue_prompt(self):
        """Test generating prompt for continuation."""
        context = GenerationContext(
            settings=self.settings,
            chapter_number=2,
            generation_mode=GenerationMode.CONTINUE,
            previous_content="这是前文内容...",
            target_word_count=1500
        )

        system, user = self.engine.generate_prompt(context)

        self.assertIn("续写", user)
        self.assertIn("这是前文内容", user)

    def test_generate_outline_prompt(self):
        """Test generating prompt for outline."""
        context = GenerationContext(
            settings=self.settings,
            chapter_number=1,
            generation_mode=GenerationMode.OUTLINE
        )

        system, user = self.engine.generate_prompt(context)

        self.assertIn("大纲", system)
        self.assertIn("设计", system)

    def test_missing_settings(self):
        """Test handling of missing settings."""
        empty_settings = ExtractedSettings()
        context = GenerationContext(
            settings=empty_settings,
            chapter_number=1
        )

        system, user = self.engine.generate_prompt(context)

        # Should use defaults
        self.assertIn("主角", user)
        self.assertIn("现代都市", user)

    def test_template_variables(self):
        """Test all template variables are populated."""
        context = GenerationContext(
            settings=self.settings,
            chapter_number=3,
            location="华山",
            mood="紧张",
            additional_instructions="添加一些打斗场面"
        )

        system, user = self.engine.generate_prompt(context)

        self.assertIn("华山", user)
        # Note: mood might not be in the default template output
        self.assertIn("打斗场面", user)


class TestCompactTemplateEngine(unittest.TestCase):
    """Test CompactTemplateEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = CompactTemplateEngine()
        self.settings = ExtractedSettings(
            characters=[CharacterProfile(name="主角", role="主角")],
            world=WorldSetting(world_type="科幻")
        )

    def test_compact_prompt(self):
        """Test compact prompt generation."""
        context = GenerationContext(
            settings=self.settings,
            chapter_number=1,
            target_word_count=1000
        )

        system, user = self.engine.generate_prompt(context)

        # Compact prompts should be shorter
        self.assertLess(len(system), 500)
        self.assertLess(len(user), 500)
        self.assertIn("科幻", user)


class TestCreateTemplateEngine(unittest.TestCase):
    """Test template engine factory function."""

    def test_default_engine(self):
        """Test creating default engine."""
        engine = create_template_engine()
        self.assertIsInstance(engine, StoryTemplateEngine)

    def test_compact_engine(self):
        """Test creating compact engine."""
        engine = create_template_engine("compact")
        self.assertIsInstance(engine, CompactTemplateEngine)

    def test_unknown_engine(self):
        """Test unknown engine type falls back to default."""
        engine = create_template_engine("unknown")
        self.assertIsInstance(engine, StoryTemplateEngine)


if __name__ == '__main__':
    unittest.main()
