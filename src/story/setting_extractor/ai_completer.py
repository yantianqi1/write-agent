"""
AI-powered setting completion module.

This module provides intelligent completion of missing story settings.
When settings are incomplete, the AI automatically generates reasonable
defaults based on existing context and story type.

This is an INTERNAL module - the completion happens transparently
without exposing the "missing settings" concept to the user.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType
)


@dataclass
class CompletionContext:
    """Context information for AI completion."""
    existing_settings: ExtractedSettings
    conversation_snippets: List[str] = field(default_factory=list)
    completion_hints: Dict[str, Any] = field(default_factory=lambda: {})
    min_completeness: float = 0.3  # Minimum completeness before auto-completion


class SettingCompleter(ABC):
    """
    Abstract base class for setting completers.

    Setting completers analyze existing (possibly incomplete) settings
    and generate reasonable completions for missing information.
    """

    @abstractmethod
    def complete(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """
        Complete the given settings by filling in missing information.

        Args:
            settings: Current (possibly incomplete) settings
            context: Additional context for completion

        Returns:
            Completed settings with reasonable defaults filled in
        """
        pass

    @abstractmethod
    def get_completion_summary(self, original: ExtractedSettings, completed: ExtractedSettings) -> List[str]:
        """
        Get a summary of what was completed.

        Args:
            original: Settings before completion
            completed: Settings after completion

        Returns:
            List of descriptions of what was auto-completed
        """
        pass


class AISettingCompleter(SettingCompleter):
    """
    AI-powered setting completer using heuristic inference.

    This completer analyzes existing settings and conversation context
    to intelligently fill in missing information with reasonable defaults.
    """

    # Default values by genre/type
    DEFAULT_WORLDS = {
        "奇幻": {
            "world_type": "奇幻世界",
            "magic_system": "存在魔法，通过咒语或媒介施法",
            "technology_level": "中世纪技术水平",
        },
        "科幻": {
            "world_type": "未来科幻世界",
            "technology_level": "高度发达的科技",
            "magic_system": None,
        },
        "都市": {
            "world_type": "现代都市",
            "era": "21世纪",
            "technology_level": "现代科技水平",
        },
        "古代": {
            "world_type": "古代社会",
            "technology_level": "前工业时代",
        },
    }

    # Default character profiles by role
    DEFAULT_CHARACTER_PROTOTYPES = {
        "主角": {
            "personality": "勇敢、善良、有成长潜力",
            "role": "主角",
        },
        "反派": {
            "personality": "狡猾、强大、有自己的动机",
            "role": "反派",
        },
        "配角": {
            "personality": "忠诚、乐于助人",
            "role": "配角",
        },
    }

    # Default style preferences
    DEFAULT_STYLE = StylePreference(
        pov="第三人称有限视角",
        tense="过去时",
        tone="平衡",
        pacing="中等",
        writing_style="流畅自然"
    )

    def __init__(self, enable_inference: bool = True):
        """
        Initialize the AI setting completer.

        Args:
            enable_inference: Whether to enable contextual inference
        """
        self.enable_inference = enable_inference
        self._completion_log: List[str] = []

    def complete(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """
        Complete settings by filling in missing information.

        This method analyzes what's present and what's missing, then
        intelligently fills gaps with reasonable defaults.

        Args:
            settings: Current (possibly incomplete) settings
            context: Additional context for completion

        Returns:
            Completed settings
        """
        self._completion_log = []
        result = settings

        # Complete world setting first (it informs other completions)
        result = self._complete_world(result, context)

        # Complete characters
        result = self._complete_characters(result, context)

        # Complete plot
        result = self._complete_plot(result, context)

        # Complete style
        result = self._complete_style(result, context)

        return result

    def _complete_world(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """Complete world setting with intelligent defaults."""
        world = settings.world if settings.world else WorldSetting()

        # Detect world type from conversation if missing
        if not world.world_type:
            world.world_type = self._infer_world_type(context)
            if world.world_type:
                self._completion_log.append(f"推断世界类型: {world.world_type}")

        # Apply defaults based on world type
        if world.world_type:
            defaults = self._get_world_defaults(world.world_type)
            for key, value in defaults.items():
                if not getattr(world, key, None):
                    setattr(world, key, value)
                    self._completion_log.append(f"补充世界观[{key}]: {value}")

        # Infer era if missing
        if not world.era:
            world.era = self._infer_era(world, context)
            if world.era:
                self._completion_log.append(f"推断时代: {world.era}")

        # Create new settings with completed world
        return ExtractedSettings(
            characters=settings.characters,
            world=world,
            plot=settings.plot,
            style=settings.style
        )

    def _complete_characters(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """Complete character profiles with intelligent defaults."""
        completed_chars = []

        for char in settings.characters:
            completed = char

            # Fill in missing name
            if not char.name:
                completed = CharacterProfile(
                    name=self._generate_character_name(char, settings, context),
                    personality=char.personality,
                    background=char.background,
                    relationships=char.relationships,
                    abilities=char.abilities,
                    appearance=char.appearance,
                    age=char.age,
                    role=char.role
                )
                if completed.name:
                    self._completion_log.append(f"为角色生成名字: {completed.name}")

            # Fill in personality based on role
            if not char.personality and char.role:
                prototype = self.DEFAULT_CHARACTER_PROTOTYPES.get(char.role, {})
                if "personality" in prototype:
                    completed.personality = prototype["personality"]
                    self._completion_log.append(f"根据角色'{char.role}'补充性格: {completed.personality}")

            # Fill in appearance based on personality and world
            if not char.appearance and settings.world:
                completed.appearance = self._generate_appearance(completed, settings.world)
                if completed.appearance:
                    self._completion_log.append(f"生成外貌描述: {completed.appearance[:30]}...")

            # Fill in background
            if not char.background:
                completed.background = self._generate_background(completed, settings.world)
                if completed.background:
                    self._completion_log.append(f"生成背景故事: {completed.background[:30]}...")

            completed_chars.append(completed)

        # Ensure at least one protagonist exists
        if not any(c.role == "主角" for c in completed_chars) and not completed_chars:
            # Create a default protagonist
            protagonist = CharacterProfile(
                name=self._generate_character_name(None, settings, context),
                role="主角",
                personality="勇敢、善良、有成长潜力",
                background="一个普通人，即将踏上非凡的旅程",
                appearance="身材中等，眼神坚毅"
            )
            completed_chars.append(protagonist)
            self._completion_log.append(f"创建默认主角: {protagonist.name}")

        return ExtractedSettings(
            characters=completed_chars,
            world=settings.world,
            plot=settings.plot,
            style=settings.style
        )

    def _complete_plot(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """Complete plot elements with intelligent defaults."""
        plot = settings.plot if settings.plot else PlotElement()

        # Infer from conversation context
        if context.conversation_snippets:
            inferred = self._infer_plot_from_context(context, settings)
            if not plot.inciting_incident and inferred.get("inciting_incident"):
                plot.inciting_incident = inferred["inciting_incident"]
                self._completion_log.append("从对话推断起因事件")

            if not plot.conflict and inferred.get("conflict"):
                plot.conflict = inferred["conflict"]
                self._completion_log.append("从对话推断主要冲突")

        # Generate default plot structure if still missing key elements
        if not plot.conflict:
            plot.conflict = self._generate_default_conflict(settings)
            self._completion_log.append(f"生成默认冲突: {plot.conflict[:30]}...")

        if not plot.inciting_incident:
            plot.inciting_incident = "一个意外的事件改变了主角的平凡生活"
            self._completion_log.append("生成默认起因事件")

        return ExtractedSettings(
            characters=settings.characters,
            world=settings.world,
            plot=plot,
            style=settings.style
        )

    def _complete_style(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """Complete style preferences with intelligent defaults."""
        style = settings.style if settings.style else StylePreference()

        # Use default style for missing elements
        defaults = {
            "pov": "第三人称有限视角",
            "tense": "过去时",
            "tone": "平衡",
            "pacing": "中等",
        }

        for key, default_value in defaults.items():
            if not getattr(style, key, None):
                setattr(style, key, default_value)
                self._completion_log.append(f"使用默认风格设置[{key}]: {default_value}")

        return ExtractedSettings(
            characters=settings.characters,
            world=settings.world,
            plot=settings.plot,
            style=style
        )

    def _infer_world_type(self, context: CompletionContext) -> Optional[str]:
        """Infer world type from conversation context."""
        if not context.conversation_snippets:
            return None

        text = " ".join(context.conversation_snippets).lower()

        # Keyword-based inference
        if any(kw in text for kw in ["魔法", "法术", "修仙", "dragon", "magic", "fantasy"]):
            return "奇幻"
        elif any(kw in text for kw in ["科技", "机器人", "太空", "未来", "robot", "sci-fi", "未来"]):
            return "科幻"
        elif any(kw in text for kw in ["古代", "朝代", "江湖", "historical"]):
            return "古代"
        else:
            return "都市"  # Default to contemporary

    def _get_world_defaults(self, world_type: str) -> Dict[str, Any]:
        """Get default world settings based on world type."""
        # Find matching default
        for key, defaults in self.DEFAULT_WORLDS.items():
            if key in world_type or world_type in key:
                return defaults.copy()
        return {}

    def _infer_era(self, world: WorldSetting, context: CompletionContext) -> Optional[str]:
        """Infer era from world and context."""
        if world.world_type:
            if "奇幻" in world.world_type:
                return "类中世纪奇幻时代"
            elif "科幻" in world.world_type or "未来" in world.world_type:
                return "未来时代"
            elif "古代" in world.world_type:
                return "古代"
        return "21世纪"  # Default

    def _generate_character_name(self, char: CharacterProfile,
                                 settings: ExtractedSettings,
                                 context: CompletionContext) -> str:
        """Generate a reasonable character name."""
        # Try to infer from conversation
        if context.conversation_snippets:
            import re
            name_pattern = re.compile(r'叫([^\s，。]{1,4})')
            for snippet in context.conversation_snippets:
                match = name_pattern.search(snippet)
                if match:
                    return match.group(1)

        # Generate based on world type
        if settings.world and settings.world.world_type:
            if "奇幻" in settings.world.world_type or "古代" in settings.world.world_type:
                names = ["云飞", "林月", "风行", "雪儿", "墨心", "青锋"]
                return names[hash(str(char)) % len(names)]
            elif "科幻" in settings.world.world_type or "未来" in settings.world.world_type:
                names = ["Alex", "Nova", "Rex", "Zara", "Kai", "Luna"]
                return names[hash(str(char)) % len(names)]

        # Default names
        names = ["小明", "小红", "李华", "王芳", "张伟", "刘洋"]
        return names[hash(str(char)) % len(names)]

    def _generate_appearance(self, char: CharacterProfile, world: WorldSetting) -> str:
        """Generate appearance description based on character and world."""
        base_appearances = [
            "身材中等，眼神坚毅",
            "身材修长，气质出众",
            "面容清秀，给人亲切感",
            "身材高大，气场强大"
        ]
        import random
        return random.choice(base_appearances)

    def _generate_background(self, char: CharacterProfile, world: WorldSetting) -> str:
        """Generate background story based on character and world."""
        if char.role == "主角":
            return "一个普通人，即将踏上非凡的旅程，面对未知的挑战"
        elif char.role == "反派":
            return "有着复杂的过去，因某些原因走上与主角对立的道路"
        else:
            return "在这个世界中有着自己的故事和立场"

    def _infer_plot_from_context(self, context: CompletionContext,
                                 settings: ExtractedSettings) -> Dict[str, Optional[str]]:
        """Infer plot elements from conversation context."""
        result = {"inciting_incident": None, "conflict": None}

        if not context.conversation_snippets:
            return result

        text = " ".join(context.conversation_snippets)

        # Simple keyword extraction for conflict
        import re
        conflict_keywords = ["反抗", "对抗", "斗争", "寻找", "拯救", "fight", "against"]
        for kw in conflict_keywords:
            if kw in text:
                result["conflict"] = f"主角需要{kw}某个目标或敌人"
                break

        return result

    def _generate_default_conflict(self, settings: ExtractedSettings) -> str:
        """Generate a default main conflict based on settings."""
        if settings.world and "奇幻" in settings.world.world_type:
            return "主角必须在黑暗势力崛起之前找到拯救世界的方法"
        elif settings.world and "科幻" in settings.world.world_type:
            return "主角需要揭露某个阴谋或真相"
        else:
            return "主角面临一个重大挑战，必须做出艰难的选择"

    def get_completion_summary(self, original: ExtractedSettings,
                              completed: ExtractedSettings) -> List[str]:
        """
        Get a summary of what was completed.

        Args:
            original: Settings before completion
            completed: Settings after completion

        Returns:
            List of descriptions of what was auto-completed
        """
        return self._completion_log.copy()

    def should_complete(self, settings: ExtractedSettings,
                       context: CompletionContext) -> Tuple[bool, str]:
        """
        Decide whether completion should be performed.

        Args:
            settings: Current settings
            context: Completion context

        Returns:
            Tuple of (should_complete, reason)
        """
        # Always complete if enabled - this is the "implicit" mode
        if not self.enable_inference:
            return False, "AI补全已禁用"

        # Check if we have at least some minimal information
        has_any_info = (
            len(settings.characters) > 0 or
            (settings.world and not settings.world.is_empty()) or
            (settings.plot and not settings.plot.is_empty()) or
            any(context.conversation_snippets)
        )

        if has_any_info:
            return True, "有足够上下文进行智能补全"

        return False, "信息不足，无法补全"


class InferenceCompleter(AISettingCompleter):
    """
    Advanced completer using contextual inference.

    This completer analyzes the conversation context more deeply
    to infer settings from story descriptions rather than explicit
    setting statements.
    """

    def __init__(self):
        """Initialize the inference completer."""
        super().__init__(enable_inference=True)

    def _infer_world_type(self, context: CompletionContext) -> Optional[str]:
        """Infer world type with more sophisticated analysis."""
        if not context.completion_hints:
            return super()._infer_world_type(context)

        # Use explicit hints if available
        if "genre" in context.completion_hints:
            return context.completion_hints["genre"]

        return super()._infer_world_type(context)

    def _infer_plot_from_context(self, context: CompletionContext,
                                 settings: ExtractedSettings) -> Dict[str, Optional[str]]:
        """Infer plot with deeper analysis."""
        result = super()._infer_plot_from_context(context, settings)

        # Check for story structure keywords
        for snippet in context.conversation_snippets:
            if "讲述" in snippet or "故事是" in snippet:
                # Extract the story description
                import re
                match = re.search(r'(?:讲述|故事是)(.{10,200})', snippet)
                if match:
                    result["conflict"] = match.group(1)[:50] + "..."
                    break

        return result


class HybridCompleter(SettingCompleter):
    """
    Hybrid completer combining rule-based and AI completion.

    This completer uses rule-based defaults for common patterns
    and falls back to AI inference for complex cases.
    """

    def __init__(self):
        """Initialize the hybrid completer."""
        self.ai_completer = InferenceCompleter()

    def complete(self, settings: ExtractedSettings, context: CompletionContext) -> ExtractedSettings:
        """Complete using hybrid approach."""
        # Use AI completer for now
        return self.ai_completer.complete(settings, context)

    def get_completion_summary(self, original: ExtractedSettings,
                              completed: ExtractedSettings) -> List[str]:
        """Get completion summary."""
        return self.ai_completer.get_completion_summary(original, completed)
