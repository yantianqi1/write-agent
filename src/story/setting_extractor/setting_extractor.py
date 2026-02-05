"""
Setting extraction from natural language input.

This module provides functionality to extract structured story settings
from user conversations using rule-based pattern matching.
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType, ExtractionRequest, ExtractionResult
)


class SettingExtractor(ABC):
    """
    Abstract base class for setting extractors.

    Setting extractors analyze user input and extract structured
    story settings (characters, world, plot, style).
    """

    @abstractmethod
    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        Extract settings from user input.

        Args:
            request: Extraction request containing user input and context

        Returns:
            ExtractionResult with extracted settings and metadata
        """
        pass


class RuleBasedExtractor(SettingExtractor):
    """
    Rule-based setting extractor using pattern matching.

    This extractor uses regular expressions and heuristic rules to
    extract structured settings from natural language input.
    """

    def __init__(self):
        """Initialize the rule-based extractor."""
        # Compile regex patterns for better performance
        self._init_character_patterns()
        self._init_world_patterns()
        self._init_plot_patterns()
        self._init_style_patterns()

    def _init_character_patterns(self):
        """Initialize regex patterns for character extraction."""
        # Name patterns: "叫X", "名为X", "名字是X", "X是一个"
        self.name_pattern = re.compile(
            r'(?:叫|名为|名字是|叫做|是)(.{1,10}?)(?:，|。|，|的|一个|一名|位|的角色|的人|$)',
            re.IGNORECASE
        )

        # Age patterns: "X岁", "age X", "X years old"
        self.age_pattern = re.compile(
            r'(\d{1,3})\s*(?:岁|years?\s*old|age\s*\d)',
            re.IGNORECASE
        )

        # Role patterns: "主角", "配角", "反派", "protagonist", "villain"
        self.role_pattern = re.compile(
            r'(?:主角|配角|反派|反派角色|男|女主角|男|女主角|protagonist|antagonist|villain|supporting)',
            re.IGNORECASE
        )

        # Personality patterns: "性格X", "personality is X", "很X"
        self.personality_pattern = re.compile(
            r'(?:性格|个性|personality|is\s+(?:very|quite|rather))\s*(.{1,30}?)(?:，|。|，|$)',
            re.IGNORECASE
        )

        # Ability patterns: "会X", "能X", "ability to X"
        self.ability_pattern = re.compile(
            r'(?:会|能|拥有|可以|ability\s+to|can)\s*(.{1,30}?)(?:，|。|，|和|以及|$)',
            re.IGNORECASE
        )

    def _init_world_patterns(self):
        """Initialize regex patterns for world setting extraction."""
        # World type: "奇幻世界", "科幻背景", "fantasy world", "sci-fi setting"
        self.world_type_pattern = re.compile(
            r'(?:奇幻|科幻|都市|历史|古代|现代|未来|末世|post-apocalyptic|'
            r'fantasy|sci.?fi|science\s+fiction|contemporary|historical|modern|future)\s*(?:世界|背景|设定|world|setting|era)',
            re.IGNORECASE
        )

        # Era: "在X朝代", "X时代", "in the X era"
        self.era_pattern = re.compile(
            r'(?:在|during|in)\s*(.{1,15}?)\s*(?:朝代|时代|时期|年代|dynasty|era|period|age)',
            re.IGNORECASE
        )

        # Magic system keywords
        self.magic_keywords = [
            "魔法", "法术", "咒语", "魔力", "修仙", "修炼", "灵气",
            "magic", "spell", "mana", "cultivation", "spiritual energy"
        ]

        # Technology level keywords
        self.tech_keywords = [
            "蒸汽朋克", "赛博朋克", "高科技", "低科技", "科技发达",
            "steampunk", "cyberpunk", "high-tech", "low-tech", "advanced technology"
        ]

    def _init_plot_patterns(self):
        """Initialize regex patterns for plot extraction."""
        # Conflict: "冲突是X", "主要矛盾X", "conflict is X"
        self.conflict_pattern = re.compile(
            r'(?:冲突|矛盾|conflict|main\s+issue)\s*(?:是|:)\s*(.{1,50}?)(?:，|。|，|$)',
            re.IGNORECASE
        )

        # Theme: "主题是X", "theme: X"
        self.theme_pattern = re.compile(
            r'(?:主题|theme)\s*(?:是|:)\s*(.{1,30}?)(?:，|。|，|$)',
            re.IGNORECASE
        )

    def _init_style_patterns(self):
        """Initialize regex patterns for style extraction."""
        # POV: "第一人称", "第三人称", "first person", "third person"
        self.pov_pattern = re.compile(
            r'(?:第一|第三|1st|3rd)\s*(?:人称|person)\s*(?:有限|全知|limited|omniscient)?',
            re.IGNORECASE
        )

        # Tense: "过去时", "现在时", "past tense", "present tense"
        self.tense_pattern = re.compile(
            r'(?:过去时|现在时|past\s+tense|present\s+tense)',
            re.IGNORECASE
        )

        # Tone: "基调X", "风格X", "tone is X"
        self.tone_keywords = {
            "轻松": ["轻松", "幽默", "搞笑", "light", "humorous", "funny"],
            "严肃": ["严肃", "正剧", "serious", "dramatic"],
            "黑暗": ["黑暗", "暗黑", "dark", "grim"],
            "温馨": ["温馨", "温暖", "heartwarming", "warm"]
        }

        # Pacing: "快节奏", "慢节奏", "fast pacing", "slow pacing"
        self.pacing_pattern = re.compile(
            r'(?:快|慢|fast|slow)\s*(?:节奏|pacing|节奏)',
            re.IGNORECASE
        )

    def extract(self, request: ExtractionRequest) -> ExtractionResult:
        """
        Extract settings from user input using rule-based patterns.

        Args:
            request: Extraction request containing user input and context

        Returns:
            ExtractionResult with extracted settings and metadata
        """
        user_input = request.user_input
        existing = request.existing_settings or ExtractedSettings()

        # Extract all setting types
        characters = self._extract_characters(user_input)
        world = self._extract_world(user_input)
        plot = self._extract_plot(user_input)
        style = self._extract_style(user_input)

        # Create extracted settings
        extracted = ExtractedSettings(
            characters=characters,
            world=world,
            plot=plot,
            style=style
        )

        # Merge with existing if in incremental mode
        if request.incremental_mode:
            extracted = existing.merge(extracted)

        # Create result (conflicts and missing info will be added by other components)
        from .models import UserIntent
        result = ExtractionResult(
            extracted_settings=extracted,
            detected_intent=UserIntent.CREATE,  # Will be overridden by intent recognizer
            involved_types=[],
            missing_info=[],
            conflicts=[],
            suggested_questions=[],
            confidence=0.7  # Default confidence for rule-based extraction
        )

        return result

    def _extract_characters(self, text: str) -> List[CharacterProfile]:
        """Extract character profiles from text."""
        characters = []

        # Try to find name
        name_match = self.name_pattern.search(text)
        name = name_match.group(1).strip() if name_match else None

        # Try to find age
        age_match = self.age_pattern.search(text)
        age = int(age_match.group(1)) if age_match else None

        # Try to find role
        role_match = self.role_pattern.search(text)
        role = role_match.group(0).strip() if role_match else None

        # Try to find personality
        personality_match = self.personality_pattern.search(text)
        personality = personality_match.group(1).strip() if personality_match else None

        # Try to find abilities
        ability_matches = self.ability_pattern.finditer(text)
        abilities = [m.group(1).strip() for m in ability_matches]

        # Only create character if we found at least a name or other info
        if name or personality or age or role or abilities:
            character = CharacterProfile(
                name=name,
                personality=personality,
                age=age,
                role=role,
                abilities=abilities
            )
            characters.append(character)

        return characters

    def _extract_world(self, text: str) -> Optional[WorldSetting]:
        """Extract world setting from text."""
        world_type = None
        era = None
        magic_system = None
        technology_level = None

        # Check world type
        world_type_match = self.world_type_pattern.search(text)
        if world_type_match:
            world_type = world_type_match.group(0).strip()

        # Check era
        era_match = self.era_pattern.search(text)
        if era_match:
            era = era_match.group(1).strip()

        # Check for magic system
        text_lower = text.lower()
        for keyword in self.magic_keywords:
            if keyword in text_lower:
                magic_system = "has_magic"
                break

        # Check technology level
        for keyword in self.tech_keywords:
            if keyword in text_lower:
                technology_level = keyword
                break

        # Only create world setting if we found something
        if world_type or era or magic_system or technology_level:
            return WorldSetting(
                world_type=world_type,
                era=era,
                magic_system=magic_system,
                technology_level=technology_level
            )

        return None

    def _extract_plot(self, text: str) -> Optional[PlotElement]:
        """Extract plot elements from text."""
        conflict = None

        # Check conflict
        conflict_match = self.conflict_pattern.search(text)
        if conflict_match:
            conflict = conflict_match.group(1).strip()

        # Check themes
        theme_matches = self.theme_pattern.finditer(text)
        themes = [m.group(1).strip() for m in theme_matches]

        # Only create plot element if we found something
        if conflict or themes:
            return PlotElement(
                conflict=conflict,
                themes=themes
            )

        return None

    def _extract_style(self, text: str) -> Optional[StylePreference]:
        """Extract style preferences from text."""
        pov = None
        tense = None
        tone = None
        pacing = None

        # Check POV
        pov_match = self.pov_pattern.search(text)
        if pov_match:
            pov = pov_match.group(0).strip()

        # Check tense
        tense_match = self.tense_pattern.search(text)
        if tense_match:
            tense = tense_match.group(0).strip()

        # Check tone
        text_lower = text.lower()
        for tone_category, keywords in self.tone_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tone = tone_category
                break

        # Check pacing
        pacing_match = self.pacing_pattern.search(text)
        if pacing_match:
            pacing = pacing_match.group(0).strip()

        # Only create style preference if we found something
        if pov or tense or tone or pacing:
            return StylePreference(
                pov=pov,
                tense=tense,
                tone=tone,
                pacing=pacing
            )

        return None
