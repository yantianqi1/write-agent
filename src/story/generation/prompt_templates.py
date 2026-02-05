"""
Prompt template system for content generation.

This module provides structured templates for generating high-quality
prompts based on story settings, chapter context, and generation mode.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

from ..setting_extractor.models import (
    ExtractedSettings, CharacterProfile, WorldSetting,
    PlotElement, StylePreference
)


class GenerationMode(Enum):
    """Mode of content generation."""
    FULL = "full"  # Generate complete chapter from scratch
    CONTINUE = "continue"  # Continue from existing content
    EXPAND = "expand"  # Expand a specific section
    REWRITE = "rewrite"  # Rewrite existing content
    OUTLINE = "outline"  # Generate chapter outline


class ContentType(Enum):
    """Type of content to generate."""
    CHAPTER = "chapter"  # Full chapter
    SCENE = "scene"  # Individual scene
    DIALOGUE = "dialogue"  # Dialogue segment
    DESCRIPTION = "description"  # Descriptive passage
    ACTION = "action"  # Action sequence


@dataclass
class GenerationContext:
    """Context for content generation."""
    settings: ExtractedSettings
    chapter_number: int = 1
    previous_content: str = ""
    chapter_outline: str = ""
    target_word_count: int = 2000
    generation_mode: GenerationMode = GenerationMode.FULL
    content_type: ContentType = ContentType.CHAPTER
    additional_instructions: str = ""
    characters_in_scene: List[str] = field(default_factory=list)
    location: str = ""
    time_of_day: str = ""
    mood: str = ""


@dataclass
class PromptTemplate:
    """A prompt template with variables."""
    system_prompt: str
    user_template: str
    variables: Dict[str, str] = field(default_factory=dict)

    def format(self, **kwargs) -> tuple[str, str]:
        """Format the template with given variables."""
        system = self.system_prompt.format(**kwargs)
        user = self.user_template.format(**kwargs)
        return system, user


class TemplateEngine(ABC):
    """Abstract base class for template engines."""

    @abstractmethod
    def generate_prompt(self, context: GenerationContext) -> tuple[str, str]:
        """
        Generate a prompt from context.

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        pass


class StoryTemplateEngine(TemplateEngine):
    """
    Template engine for story content generation.

    Generates high-quality prompts tailored to the story's settings,
    characters, and current context.
    """

    # Base system prompt
    BASE_SYSTEM_PROMPT = """你是一位专业的小说作家，擅长创作引人入胜的故事内容。

你的任务是：
1. 严格遵循提供的故事设定和世界观
2. 保持角色性格和行为的一致性
3. 创作生动、富有画面感的场景描写
4. 编写自然流畅的对话
5. 保持情节的逻辑连贯性

写作要求：
- 使用{pov}进行叙述
- 采用{tense}写作
- 保持{tone}基调
- 控制节奏为{pacing}
- 目标字数约{word_count}字

请直接开始创作内容，不要添加任何解释或元评论。"""

    def __init__(self):
        """Initialize the template engine."""
        self._init_templates()

    def _init_templates(self):
        """Initialize prompt templates for different modes."""
        self.templates = {
            GenerationMode.FULL: PromptTemplate(
                system_prompt=self.BASE_SYSTEM_PROMPT,
                user_template="""# 故事设定

## 世界观
- 世界类型：{world_type}
- 时代背景：{era}
{magic_system}
{technology_level}

## 主角信息
- 姓名：{protagonist_name}
- 身份：{protagonist_role}
- 性格：{protagonist_personality}
- 外貌：{protagonist_appearance}
{protagonist_background}

## 故事情节
- 核心冲突：{conflict}
- 当前阶段：{plot_stage}

## 本章要求
- 章节：第{chapter}章
- 场景：{location}
- 登场角色：{characters_in_scene}
- 特殊要求：{additional_instructions}

请创作第{chapter}章的内容。"""
            ),

            GenerationMode.CONTINUE: PromptTemplate(
                system_prompt=self.BASE_SYSTEM_PROMPT,
                user_template="""# 续写要求

## 故事设定概要
- 世界类型：{world_type}
- 主角：{protagonist_name}（{protagonist_personality}）
- 核心冲突：{conflict}

## 前文内容
{previous_content}

## 续写要求
- 继续第{chapter}章的故事
- 保持情节连贯和人物一致性
- 目标字数约{word_count}字
{additional_instructions}

请从前文结束的地方继续创作。"""
            ),

            GenerationMode.REWRITE: PromptTemplate(
                system_prompt="""你是一位专业的小说编辑和作家。

你的任务是：
1. 理解用户的修改意图
2. 重写指定内容
3. 保持故事设定的整体一致性
4. 提升内容的表达效果

请直接输出重写后的内容，不要添加任何解释。""",
                user_template="""# 重写要求

## 故事设定
- 世界类型：{world_type}
- 主角：{protagonist_name}（{protagonist_personality}）

## 原文内容
{original_content}

## 修改要求
{modification_request}

## 附加说明
{additional_instructions}

请根据修改要求重写上述内容。"""
            ),

            GenerationMode.EXPAND: PromptTemplate(
                system_prompt=self.BASE_SYSTEM_PROMPT,
                user_template="""# 扩写要求

## 故事设定
- 世界类型：{world_type}
- 主角：{protagonist_name}（{protagonist_personality}）

## 基础内容
{base_content}

## 扩写要求
- 扩展细节描写
- 增加场景氛围
- 丰富人物心理活动
- 目标字数约{word_count}字

## 附加说明
{additional_instructions}

请对上述内容进行扩写。"""
            ),

            GenerationMode.OUTLINE: PromptTemplate(
                system_prompt="""你是一位专业的故事大纲设计师。

请根据提供的故事设定，设计详细的章节大纲。

大纲要求：
1. 明确本章的主要事件
2. 标注关键情节节点
3. 列出场登角色
4. 说明本章的情节推进作用

请以结构化的格式输出大纲。""",
                user_template="""# 大纲设计要求

## 故事设定
- 世界类型：{world_type}
- 时代背景：{era}
- 主角：{protagonist_name}（{protagonist_role}）
- 性格：{protagonist_personality}

## 故事主线
- 核心冲突：{conflict}
- 起因事件：{inciting_incident}
{themes}

## 本章定位
- 章节编号：第{chapter}章
- 前情概要：{previous_summary}
- 本章目标：{chapter_goal}

## 附加要求
{additional_instructions}

请设计第{chapter}章的详细大纲。"""
            ),
        }

    def generate_prompt(self, context: GenerationContext) -> tuple[str, str]:
        """Generate a prompt from context."""
        template = self.templates.get(context.generation_mode, self.templates[GenerationMode.FULL])

        # Prepare variables
        variables = self._prepare_variables(context)

        # Format template
        return template.format(**variables)

    def _prepare_variables(self, context: GenerationContext) -> Dict[str, str]:
        """Prepare template variables from context."""
        settings = context.settings
        variables = {}

        # Style variables
        style = settings.style or self._default_style()
        variables.update({
            "pov": style.pov or "第三人称有限视角",
            "tense": style.tense or "过去时",
            "tone": style.tone or "平衡",
            "pacing": style.pacing or "中等",
            "word_count": context.target_word_count,
        })

        # World variables
        world = settings.world or WorldSetting()
        variables.update({
            "world_type": world.world_type or "现代都市",
            "era": world.era or "21世纪",
            "magic_system": f"- 魔法系统：{world.magic_system}" if world.magic_system else "",
            "technology_level": f"- 科技水平：{world.technology_level}" if world.technology_level else "",
        })

        # Character variables
        protagonist = self._get_protagonist(settings)
        if protagonist:
            variables.update({
                "protagonist_name": protagonist.name or "主角",
                "protagonist_role": protagonist.role or "主角",
                "protagonist_personality": protagonist.personality or "勇敢、善良",
                "protagonist_appearance": protagonist.appearance or "普通外貌",
                "protagonist_background": f"- 背景：{protagonist.background}" if protagonist.background else "",
            })
        else:
            variables.update({
                "protagonist_name": "主角",
                "protagonist_role": "主角",
                "protagonist_personality": "勇敢、善良",
                "protagonist_appearance": "普通外貌",
                "protagonist_background": "",
            })

        # Plot variables
        plot = settings.plot or PlotElement()
        variables.update({
            "conflict": plot.conflict or "主角面临重大挑战",
            "inciting_incident": plot.inciting_incident or "意外事件改变了主角的生活",
            "plot_stage": self._infer_plot_stage(context.chapter_number),
            "themes": "\n".join(f"- 主题：{t}" for t in plot.themes) if plot.themes else "",
        })

        # Context variables
        variables.update({
            "chapter": context.chapter_number,
            "location": context.location or "待定场景",
            "characters_in_scene": ", ".join(context.characters_in_scene) if context.characters_in_scene else "主角",
            "previous_content": context.previous_content or "",
            "previous_summary": self._summarize_previous(context.previous_content),
            "chapter_goal": self._infer_chapter_goal(context.chapter_number, context),
            "additional_instructions": context.additional_instructions or "",
        })

        # Special handling for different modes
        if context.generation_mode == GenerationMode.REWRITE:
            variables["original_content"] = context.previous_content
            variables["modification_request"] = context.additional_instructions

        if context.generation_mode == GenerationMode.EXPAND:
            variables["base_content"] = context.previous_content

        return variables

    def _get_protagonist(self, settings: ExtractedSettings) -> Optional[CharacterProfile]:
        """Get the protagonist character."""
        for char in settings.characters:
            if char.role == "主角":
                return char
        return settings.characters[0] if settings.characters else None

    def _default_style(self) -> StylePreference:
        """Get default style preferences."""
        return StylePreference(
            pov="第三人称有限视角",
            tense="过去时",
            tone="平衡",
            pacing="中等"
        )

    def _infer_plot_stage(self, chapter_number: int) -> str:
        """Infer the current plot stage based on chapter number."""
        if chapter_number == 1:
            return "开篇 - 介绍主角和世界观，引发事件"
        elif chapter_number <= 3:
            return "发展 - 主角接受挑战，开始旅程"
        elif chapter_number <= 6:
            return "发展 - 遭遇困难，逐渐成长"
        else:
            return "推进 - 情节向高潮发展"

    def _infer_chapter_goal(self, chapter_number: int, context: GenerationContext) -> str:
        """Infer the goal of this chapter."""
        if chapter_number == 1:
            return "介绍主角，引发事件，建立故事基调"
        elif context.previous_content:
            return "推进情节，发展人物关系，为后续铺垫"
        else:
            return "继续故事发展，保持情节连贯"

    def _summarize_previous(self, content: str) -> str:
        """Create a brief summary of previous content."""
        if not content:
            return "故事开篇"
        # Take first ~200 characters as summary
        return content[:200] + ("..." if len(content) > 200 else "")


class CompactTemplateEngine(StoryTemplateEngine):
    """
    A more compact template engine for faster generation.

    Uses shorter prompts while maintaining quality.
    """

    COMPACT_SYSTEM = """你是专业小说作家。根据设定创作内容，要求：
- 保持{pov}、{tense}、{tone}基调
- 目标字数约{word_count}字
- 直接输出内容，无需解释"""

    COMPACT_USER = """设定：{world_type}世界，主角{protagonist_name}（{protagonist_personality}）
冲突：{conflict}
章节：第{chapter}章
{additional_instructions}

开始创作："""

    def __init__(self):
        """Initialize the compact template engine."""
        super().__init__()

    def generate_prompt(self, context: GenerationContext) -> tuple[str, str]:
        """Generate a compact prompt."""
        variables = self._prepare_variables(context)

        system = self.COMPACT_SYSTEM.format(**variables)
        user = self.COMPACT_USER.format(**variables)

        return system, user


def create_template_engine(engine_type: str = "default") -> TemplateEngine:
    """
    Factory function to create template engines.

    Args:
        engine_type: Type of engine ("default" or "compact")

    Returns:
        Configured TemplateEngine
    """
    if engine_type == "compact":
        return CompactTemplateEngine()
    return StoryTemplateEngine()
