"""
Unit tests for content generator.

Tests the LLMContentGenerator, StoryGenerator, and
related content generation functionality.
"""

import unittest
import asyncio

from story.generation.content_generator import (
    GenerationRequest,
    GenerationResult,
    ContentGenerator,
    LLMContentGenerator,
    ChapterContent,
    StoryGenerator,
    create_content_generator,
    create_story_generator
)
from story.generation.prompt_templates import (
    GenerationContext,
    GenerationMode
)
from story.llm.base import (
    MockLLMProvider,
    LLMRequest,
    Message,
    MessageRole
)
from story.setting_extractor.models import (
    ExtractedSettings,
    CharacterProfile,
    WorldSetting,
    PlotElement
)


class TestGenerationRequest(unittest.TestCase):
    """Test GenerationRequest dataclass."""

    def test_default_request(self):
        """Test request with defaults."""
        settings = ExtractedSettings()
        request = GenerationRequest(settings=settings)

        self.assertEqual(request.chapter_number, 1)
        self.assertEqual(request.generation_mode, GenerationMode.FULL)
        self.assertEqual(request.target_word_count, 2000)
        self.assertEqual(request.temperature, 0.7)

    def test_full_request(self):
        """Test request with all fields."""
        settings = ExtractedSettings()
        request = GenerationRequest(
            settings=settings,
            chapter_number=5,
            generation_mode=GenerationMode.CONTINUE,
            target_word_count=3000,
            previous_content="Previous...",
            additional_instructions="Make it exciting"
        )

        self.assertEqual(request.chapter_number, 5)
        self.assertEqual(request.generation_mode, GenerationMode.CONTINUE)
        self.assertEqual(request.target_word_count, 3000)


class TestGenerationResult(unittest.TestCase):
    """Test GenerationResult dataclass."""

    def test_result_creation(self):
        """Test creating a result."""
        result = GenerationResult(
            content="Generated content...",
            chapter_number=1,
            word_count=100,
            generation_mode=GenerationMode.FULL
        )

        self.assertEqual(result.content, "Generated content...")
        self.assertEqual(result.chapter_number, 1)
        self.assertEqual(result.word_count, 100)

    def test_result_to_dict(self):
        """Test converting result to dict."""
        result = GenerationResult(
            content="Content",
            chapter_number=1,
            word_count=50,
            generation_mode=GenerationMode.FULL,
            metadata={"model": "test"}
        )

        d = result.to_dict()
        self.assertEqual(d["content"], "Content")
        self.assertEqual(d["chapter_number"], 1)
        self.assertEqual(d["generation_mode"], "full")


class TestChapterContent(unittest.TestCase):
    """Test ChapterContent dataclass."""

    def test_chapter_creation(self):
        """Test creating chapter content."""
        chapter = ChapterContent(
            chapter_number=1,
            title="第一章",
            content="Chapter content...",
            word_count=100
        )

        self.assertEqual(chapter.chapter_number, 1)
        self.assertEqual(chapter.title, "第一章")

    def test_chapter_to_dict(self):
        """Test converting chapter to dict."""
        chapter = ChapterContent(
            chapter_number=1,
            title="第一章",
            content="Content",
            word_count=50,
            characters=["Alice", "Bob"]
        )

        d = chapter.to_dict()
        self.assertEqual(d["chapter_number"], 1)
        self.assertEqual(d["characters"], ["Alice", "Bob"])


class TestLLMContentGenerator(unittest.TestCase):
    """Test LLMContentGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm = MockLLMProvider()
        self.generator = LLMContentGenerator(self.llm)

        self.settings = ExtractedSettings(
            characters=[
                CharacterProfile(
                    name="李明",
                    role="主角",
                    personality="勇敢"
                )
            ],
            world=WorldSetting(world_type="现代"),
            plot=PlotElement(conflict="李明需要解决难题")
        )

    def test_generate(self):
        """Test basic generation."""
        request = GenerationRequest(
            settings=self.settings,
            chapter_number=1,
            target_word_count=500
        )

        result = self.generator.generate(request)

        self.assertIsNotNone(result.content)
        self.assertEqual(result.chapter_number, 1)
        self.assertGreater(result.word_count, 0)
        self.assertEqual(result.generation_mode, GenerationMode.FULL)

    def test_generate_with_mode(self):
        """Test generation with different modes."""
        for mode in [GenerationMode.FULL, GenerationMode.CONTINUE, GenerationMode.OUTLINE]:
            request = GenerationRequest(
                settings=self.settings,
                chapter_number=1,
                generation_mode=mode
            )

            result = self.generator.generate(request)
            self.assertEqual(result.generation_mode, mode)

    def test_generation_history(self):
        """Test generation history tracking."""
        request = GenerationRequest(settings=self.settings, chapter_number=1)

        self.generator.generate(request)
        self.generator.generate(request)

        history = self.generator.get_generation_history()
        self.assertEqual(len(history), 2)

    def test_clear_history(self):
        """Test clearing generation history."""
        request = GenerationRequest(settings=self.settings, chapter_number=1)
        self.generator.generate(request)

        self.generator.clear_history()
        history = self.generator.get_generation_history()
        self.assertEqual(len(history), 0)

    def test_word_counting(self):
        """Test word counting."""
        # Test with mixed Chinese-English
        text = "Hello 世界! This is a test. 测试文本。"
        count = self.generator._count_words(text)

        # Should count both Chinese characters and English words
        self.assertGreater(count, 0)

    def test_async_generate(self):
        """Test async generation."""
        async def run_test():
            request = GenerationRequest(
                settings=self.settings,
                chapter_number=1
            )

            result = await self.generator.generate_async(request)
            self.assertIsNotNone(result.content)

        asyncio.run(run_test())

    def test_stream_generate(self):
        """Test streaming generation."""
        async def run_test():
            request = GenerationRequest(
                settings=self.settings,
                chapter_number=1,
                target_word_count=200
            )

            chunks = []
            async for chunk in self.generator.generate_stream(request):
                chunks.append(chunk)

            self.assertGreater(len(chunks), 0)

        asyncio.run(run_test())


class TestStoryGenerator(unittest.TestCase):
    """Test StoryGenerator."""

    def setUp(self):
        """Set up test fixtures."""
        self.llm = MockLLMProvider()
        # StoryGenerator expects a ContentGenerator, not LLMProvider
        self.content_gen = LLMContentGenerator(self.llm)
        self.story_gen = StoryGenerator(self.content_gen, auto_outline=False)

        self.settings = ExtractedSettings(
            characters=[
                CharacterProfile(
                    name="云飞",
                    role="主角",
                    personality="勇敢"
                )
            ],
            world=WorldSetting(world_type="武侠"),
            plot=PlotElement(conflict="云飞要报仇")
        )

    def test_generate_chapter(self):
        """Test generating a chapter."""
        chapter = self.story_gen.generate_chapter(
            settings=self.settings,
            chapter_number=1
        )

        self.assertEqual(chapter.chapter_number, 1)
        self.assertIsNotNone(chapter.content)
        self.assertGreater(chapter.word_count, 0)

    def test_generate_multiple_chapters(self):
        """Test generating multiple chapters."""
        for i in range(1, 4):
            chapter = self.story_gen.generate_chapter(
                settings=self.settings,
                chapter_number=i
            )
            self.assertEqual(chapter.chapter_number, i)

    def test_continue_from_last(self):
        """Test continuing from last chapter."""
        # Generate first chapter
        self.story_gen.generate_chapter(
            settings=self.settings,
            chapter_number=1
        )

        # Continue
        chapter = self.story_gen.continue_from_last(
            settings=self.settings
        )

        self.assertEqual(chapter.chapter_number, 2)

    def test_rewrite_chapter(self):
        """Test rewriting a chapter."""
        # Generate original
        original = self.story_gen.generate_chapter(
            settings=self.settings,
            chapter_number=1
        )
        original_content = original.content

        # Rewrite
        rewritten = self.story_gen.rewrite_chapter(
            chapter_number=1,
            modification_instruction="Make it more dramatic",
            settings=self.settings
        )

        self.assertEqual(rewritten.chapter_number, 1)
        # Content should be different (in real usage)
        self.assertIsNotNone(rewritten.content)

    def test_expand_section(self):
        """Test expanding a section."""
        base_text = "这是一段简短的文字。"

        expanded = self.story_gen.expand_section(
            chapter_number=1,
            settings=self.settings,
            section_text=base_text,
            target_words=300
        )

        self.assertIsNotNone(expanded)

    def test_get_chapter(self):
        """Test retrieving a chapter."""
        self.story_gen.generate_chapter(
            settings=self.settings,
            chapter_number=1
        )

        chapter = self.story_gen.get_chapter(1)
        self.assertIsNotNone(chapter)
        self.assertEqual(chapter.chapter_number, 1)

    def test_get_all_chapters(self):
        """Test getting all chapters."""
        for i in range(1, 4):
            self.story_gen.generate_chapter(
                settings=self.settings,
                chapter_number=i
            )

        chapters = self.story_gen.get_all_chapters()
        self.assertEqual(len(chapters), 3)
        self.assertEqual(chapters[0].chapter_number, 1)
        self.assertEqual(chapters[1].chapter_number, 2)
        self.assertEqual(chapters[2].chapter_number, 3)

    def test_get_full_story(self):
        """Test getting full story."""
        self.story_gen.generate_chapter(
            settings=self.settings,
            chapter_number=1,
            target_word_count=100
        )

        full_story = self.story_gen.get_full_story()
        self.assertGreater(len(full_story), 0)

    def test_get_story_stats(self):
        """Test getting story statistics."""
        for i in range(1, 4):
            self.story_gen.generate_chapter(
                settings=self.settings,
                chapter_number=i,
                target_word_count=500
            )

        stats = self.story_gen.get_story_stats()
        self.assertEqual(stats["total_chapters"], 3)
        self.assertGreater(stats["total_words"], 0)
        self.assertGreater(stats["avg_words_per_chapter"], 0)
        self.assertEqual(stats["chapter_numbers"], [1, 2, 3])


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions."""

    def test_create_content_generator(self):
        """Test creating content generator."""
        llm = MockLLMProvider()
        generator = create_content_generator(llm)

        self.assertIsInstance(generator, LLMContentGenerator)

    def test_create_story_generator(self):
        """Test creating story generator."""
        llm = MockLLMProvider()
        story_gen = create_story_generator(llm)

        self.assertIsInstance(story_gen, StoryGenerator)


if __name__ == '__main__':
    unittest.main()
