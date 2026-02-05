"""
Content generation engine.

This module provides the main content generation engine that integrates
LLM providers with prompt templates to generate story content.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from ..llm.base import LLMProvider, LLMRequest, LLMResponse, LLMStreamChunk, Message, MessageRole
from ..setting_extractor.models import ExtractedSettings
from .prompt_templates import (
    GenerationContext, GenerationMode, ContentType,
    TemplateEngine, StoryTemplateEngine, create_template_engine
)


@dataclass
class GenerationRequest:
    """Request for content generation."""
    settings: ExtractedSettings
    chapter_number: int = 1
    generation_mode: GenerationMode = GenerationMode.FULL
    target_word_count: int = 2000
    previous_content: str = ""
    chapter_outline: str = ""
    additional_instructions: str = ""
    characters_in_scene: List[str] = field(default_factory=list)
    location: str = ""
    mood: str = ""
    temperature: float = 0.7
    stream: bool = False


@dataclass
class GenerationResult:
    """Result of content generation."""
    content: str
    chapter_number: int
    word_count: int
    generation_mode: GenerationMode
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "chapter_number": self.chapter_number,
            "word_count": self.word_count,
            "generation_mode": self.generation_mode.value,
            "metadata": self.metadata.copy()
        }


class ContentGenerator(ABC):
    """Abstract base class for content generators."""

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResult:
        """Generate content based on request."""
        pass

    @abstractmethod
    async def generate_async(self, request: GenerationRequest) -> GenerationResult:
        """Generate content asynchronously."""
        pass

    @abstractmethod
    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Generate content with streaming."""
        pass


class LLMContentGenerator(ContentGenerator):
    """
    Content generator powered by LLM.

    Integrates prompt templates with LLM providers to generate
    high-quality story content.
    """

    def __init__(self,
                 llm_provider: LLMProvider,
                 template_engine: Optional[TemplateEngine] = None):
        """
        Initialize the content generator.

        Args:
            llm_provider: LLM provider for content generation
            template_engine: Optional template engine (defaults to StoryTemplateEngine)
        """
        self.llm_provider = llm_provider
        self.template_engine = template_engine or StoryTemplateEngine()
        self.generation_history: List[GenerationResult] = []

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate content based on request.

        Args:
            request: Generation request

        Returns:
            GenerationResult with generated content
        """
        # Create generation context
        context = self._create_context(request)

        # Generate prompts
        system_prompt, user_prompt = self.template_engine.generate_prompt(context)

        # Build LLM request
        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_prompt)
        ]

        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.target_word_count * 2,  # Rough token estimate
        )

        # Generate content
        llm_response = self.llm_provider.generate(llm_request)

        # Create result
        result = GenerationResult(
            content=llm_response.content,
            chapter_number=request.chapter_number,
            word_count=self._count_words(llm_response.content),
            generation_mode=request.generation_mode,
            metadata={
                "model": llm_response.model,
                "finish_reason": llm_response.finish_reason,
                "usage": llm_response.usage,
                "prompt_tokens": llm_response.usage.get("prompt_tokens", 0),
                "completion_tokens": llm_response.usage.get("completion_tokens", 0),
            }
        )

        # Store in history
        self.generation_history.append(result)

        return result

    async def generate_async(self, request: GenerationRequest) -> GenerationResult:
        """Generate content asynchronously."""
        context = self._create_context(request)
        system_prompt, user_prompt = self.template_engine.generate_prompt(context)

        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_prompt)
        ]

        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.target_word_count * 2,
        )

        llm_response = await self.llm_provider.generate_async(llm_request)

        result = GenerationResult(
            content=llm_response.content,
            chapter_number=request.chapter_number,
            word_count=self._count_words(llm_response.content),
            generation_mode=request.generation_mode,
            metadata={
                "model": llm_response.model,
                "finish_reason": llm_response.finish_reason,
                "usage": llm_response.usage,
            }
        )

        self.generation_history.append(result)
        return result

    async def generate_stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Generate content with streaming."""
        context = self._create_context(request)
        system_prompt, user_prompt = self.template_engine.generate_prompt(context)

        messages = [
            Message(role=MessageRole.SYSTEM, content=system_prompt),
            Message(role=MessageRole.USER, content=user_prompt)
        ]

        llm_request = LLMRequest(
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.target_word_count * 2,
        )

        full_content = []

        async for chunk in self.llm_provider.stream(llm_request):
            if not chunk.is_final:
                full_content.append(chunk.content)
                yield chunk.content

        # Store complete result
        final_content = "".join(full_content)
        result = GenerationResult(
            content=final_content,
            chapter_number=request.chapter_number,
            word_count=self._count_words(final_content),
            generation_mode=request.generation_mode,
            metadata={"streamed": True}
        )
        self.generation_history.append(result)

    def _create_context(self, request: GenerationRequest) -> GenerationContext:
        """Create GenerationContext from GenerationRequest."""
        return GenerationContext(
            settings=request.settings,
            chapter_number=request.chapter_number,
            generation_mode=request.generation_mode,
            target_word_count=request.target_word_count,
            previous_content=request.previous_content,
            chapter_outline=request.chapter_outline,
            additional_instructions=request.additional_instructions,
            characters_in_scene=request.characters_in_scene,
            location=request.location,
            mood=request.mood
        )

    def _count_words(self, text: str) -> int:
        """Count words in mixed Chinese-English text."""
        # Count Chinese characters
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        # Count English words
        english_words = len(text.split()) - chinese_chars
        return chinese_chars + english_words

    def get_generation_history(self) -> List[GenerationResult]:
        """Get history of all generations."""
        return self.generation_history.copy()

    def clear_history(self) -> None:
        """Clear generation history."""
        self.generation_history.clear()


@dataclass
class ChapterContent:
    """Content of a generated chapter."""
    chapter_number: int
    title: str = ""
    content: str = ""
    word_count: int = 0
    summary: str = ""
    outline: str = ""
    characters: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    created_at: str = ""
    modified_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "content": self.content,
            "word_count": self.word_count,
            "summary": self.summary,
            "outline": self.outline,
            "characters": self.characters.copy(),
            "locations": self.locations.copy(),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }


class StoryGenerator:
    """
    High-level story generation orchestrator.

    Manages the overall story generation process including
    chapter planning, content generation, and consistency tracking.
    """

    def __init__(self,
                 content_generator: ContentGenerator,
                 auto_outline: bool = True):
        """
        Initialize the story generator.

        Args:
            content_generator: Underlying content generator
            auto_outline: Whether to auto-generate outlines before chapters
        """
        self.content_generator = content_generator
        self.auto_outline = auto_outline
        self.chapters: Dict[int, ChapterContent] = {}
        self.story_outline: List[str] = []

    def generate_chapter(self,
                        settings: ExtractedSettings,
                        chapter_number: int = 1,
                        mode: GenerationMode = GenerationMode.FULL,
                        **kwargs) -> ChapterContent:
        """
        Generate a chapter.

        Args:
            settings: Story settings
            chapter_number: Chapter number to generate
            mode: Generation mode (can also be passed as generation_mode in kwargs)
            **kwargs: Additional generation parameters

        Returns:
            ChapterContent with generated content
        """
        # Get previous chapter for context
        previous_content = ""
        if chapter_number > 1 and (chapter_number - 1) in self.chapters:
            previous_content = self.chapters[chapter_number - 1].content[-500:]

        # Remove conflicting keys from kwargs before passing to GenerationRequest
        safe_kwargs = {k: v for k, v in kwargs.items()
                      if k not in ('settings', 'chapter_number', 'generation_mode', 'mode',
                                   'previous_content', 'chapter_outline', 'target_word_count',
                                   'temperature', 'additional_instructions', 'characters_in_scene',
                                   'location', 'mood', 'stream')}

        # Optionally generate outline first
        outline = ""
        if self.auto_outline and mode == GenerationMode.FULL:
            outline_request = GenerationRequest(
                settings=settings,
                chapter_number=chapter_number,
                generation_mode=GenerationMode.OUTLINE,
                target_word_count=500,
                previous_content=previous_content,
                **safe_kwargs
            )
            outline_result = self.content_generator.generate(outline_request)
            outline = outline_result.content

        # Generate chapter content
        request = GenerationRequest(
            settings=settings,
            chapter_number=chapter_number,
            generation_mode=mode,
            previous_content=previous_content,
            chapter_outline=outline,
            **safe_kwargs
        )

        result = self.content_generator.generate(request)

        # Create chapter content
        from datetime import datetime
        now = datetime.now().isoformat()

        chapter = ChapterContent(
            chapter_number=chapter_number,
            title=f"第{chapter_number}章",
            content=result.content,
            word_count=result.word_count,
            outline=outline,
            created_at=now,
            modified_at=now
        )

        self.chapters[chapter_number] = chapter
        return chapter

    def continue_from_last(self,
                          settings: ExtractedSettings,
                          **kwargs) -> ChapterContent:
        """Continue generating from the last chapter."""
        next_chapter = len(self.chapters) + 1
        return self.generate_chapter(
            settings, next_chapter, GenerationMode.CONTINUE, **kwargs
        )

    def rewrite_chapter(self,
                       chapter_number: int,
                       modification_instruction: str,
                       settings: ExtractedSettings) -> ChapterContent:
        """Rewrite a chapter based on modification instruction."""
        if chapter_number not in self.chapters:
            raise ValueError(f"Chapter {chapter_number} not found")

        original_chapter = self.chapters[chapter_number]

        request = GenerationRequest(
            settings=settings,
            chapter_number=chapter_number,
            generation_mode=GenerationMode.REWRITE,
            previous_content=original_chapter.content,
            additional_instructions=modification_instruction
        )

        result = self.content_generator.generate(request)

        from datetime import datetime
        chapter = ChapterContent(
            chapter_number=chapter_number,
            title=original_chapter.title,
            content=result.content,
            word_count=result.word_count,
            outline=original_chapter.outline,
            created_at=original_chapter.created_at,
            modified_at=datetime.now().isoformat()
        )

        self.chapters[chapter_number] = chapter
        return chapter

    def expand_section(self,
                      chapter_number: int,
                      settings: ExtractedSettings,
                      section_text: str = "",
                      target_words: int = 500) -> str:
        """Expand a specific section of a chapter."""
        request = GenerationRequest(
            settings=settings,
            chapter_number=chapter_number,
            generation_mode=GenerationMode.EXPAND,
            previous_content=section_text,
            target_word_count=target_words
        )

        result = self.content_generator.generate(request)
        return result.content

    def get_chapter(self, chapter_number: int) -> Optional[ChapterContent]:
        """Get a chapter by number."""
        return self.chapters.get(chapter_number)

    def get_all_chapters(self) -> List[ChapterContent]:
        """Get all chapters in order."""
        return [self.chapters[i] for i in sorted(self.chapters.keys())]

    def get_full_story(self) -> str:
        """Get the full story as a single string."""
        chapters = self.get_all_chapters()
        return "\n\n".join(chapter.content for chapter in chapters)

    def get_story_stats(self) -> Dict[str, Any]:
        """Get statistics about the generated story."""
        chapters = self.get_all_chapters()
        total_words = sum(ch.word_count for ch in chapters)

        return {
            "total_chapters": len(chapters),
            "total_words": total_words,
            "avg_words_per_chapter": total_words // len(chapters) if chapters else 0,
            "chapter_numbers": sorted(self.chapters.keys()),
        }


def create_content_generator(llm_provider: LLMProvider,
                            template_engine: Optional[TemplateEngine] = None) -> ContentGenerator:
    """
    Factory function to create content generators.

    Args:
        llm_provider: LLM provider to use
        template_engine: Optional template engine

    Returns:
        Configured ContentGenerator
    """
    return LLMContentGenerator(llm_provider, template_engine)


def create_story_generator(llm_provider: LLMProvider,
                          auto_outline: bool = True) -> StoryGenerator:
    """
    Factory function to create story generators.

    Args:
        llm_provider: LLM provider to use
        auto_outline: Whether to auto-generate outlines

    Returns:
        Configured StoryGenerator
    """
    content_gen = create_content_generator(llm_provider)
    return StoryGenerator(content_gen, auto_outline)
