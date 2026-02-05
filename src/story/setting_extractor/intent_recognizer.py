"""
Intent recognition for conversational setting extraction.

This module provides functionality to identify user intents and involved
setting types from natural language input.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set, Tuple
from .models import UserIntent, SettingType


class IntentRecognizer(ABC):
    """
    Abstract base class for intent recognizers.

    Intent recognizers analyze user input to determine:
    1. What the user wants to do (create/modify/query/setting/chat)
    2. Which setting types are involved (character/world/plot/style)
    """

    @abstractmethod
    def recognize_intent(self, user_input: str) -> UserIntent:
        """
        Recognize the user's primary intent.

        Args:
            user_input: User's natural language input

        Returns:
            Detected UserIntent
        """
        pass

    @abstractmethod
    def recognize_setting_types(self, user_input: str) -> List[SettingType]:
        """
        Recognize which setting types are mentioned in the input.

        Args:
            user_input: User's natural language input

        Returns:
            List of involved SettingType (may be empty)
        """
        pass

    @abstractmethod
    def recognize(self, user_input: str) -> Tuple[UserIntent, List[SettingType]]:
        """
        Recognize both intent and setting types in one call.

        Args:
            user_input: User's natural language input

        Returns:
            Tuple of (UserIntent, List[SettingType])
        """
        pass


class KeywordIntentRecognizer(IntentRecognizer):
    """
    Rule-based intent recognizer using keyword matching.

    This recognizer uses predefined keyword lists to identify user intents
    and involved setting types. It's simple, fast, and easily extensible.
    """

    # Intent keywords (Chinese and English)
    INTENT_KEYWORDS = {
        UserIntent.CREATE: [
            "create", "add", "make", "new", "start", "begin",
            "创建", "添加", "增加", "新建", "生成", "开始", "设立", "设定"
        ],
        UserIntent.MODIFY: [
            "change", "modify", "update", "edit", "alter", "revise",
            "修改", "改变", "更新", "调整", "编辑", "改", "换"
        ],
        UserIntent.QUERY: [
            "what", "how", "show", "tell", "describe", "explain",
            "什么", "怎么", "如何", "显示", "告诉", "说明", "介绍", "查询", "看看"
        ],
        UserIntent.SETTING: [
            "config", "preference", "option", "setting",
            "配置", "设置", "选项", "偏好"
        ]
    }

    # Setting type keywords
    SETTING_TYPE_KEYWORDS = {
        SettingType.CHARACTER: [
            "character", "protagonist", "hero", "villain", "role", "person",
            "npc", "persona", "figure", "who", "name", "he", "she", "they",
            "角色", "人物", "主角", "配角", "反派", "主角", "他", "她", "谁",
            "性格", "外貌", "背景", "能力", "关系"
        ],
        SettingType.WORLD: [
            "world", "setting", "environment", "place", "location", "universe",
            "realm", "dimension", "magic", "technology", "geography", "era",
            "世界", "设定", "环境", "地点", "位置", "宇宙", "位面", "维度",
            "魔法", "科技", "地理", "时代", "世界观", "背景"
        ],
        SettingType.PLOT: [
            "plot", "story", "narrative", "conflict", "climax", "ending",
            "beginning", "middle", "ending", "twist", "event", "action",
            "情节", "故事", "冲突", "高潮", "结局", "开始", "发展", "转折",
            "事件", "剧情", "主线", "支线"
        ],
        SettingType.STYLE: [
            "style", "tone", "voice", "pov", "perspective", "narrative",
            "writing", "genre", "mood", "atmosphere", "pacing", "tense",
            "风格", "基调", "语气", "视角", "叙述", "文体", "流派", "氛围",
            "节奏", "时态", "写法"
        ]
    }

    def __init__(self, default_intent: UserIntent = UserIntent.CHAT):
        """
        Initialize the keyword intent recognizer.

        Args:
            default_intent: Default intent when no keywords match (default: CHAT)
        """
        self.default_intent = default_intent

    def recognize_intent(self, user_input: str) -> UserIntent:
        """
        Recognize the user's primary intent using keyword matching.

        The method checks for intent keywords in order of priority:
        1. SETTING (configuration changes)
        2. MODIFY (modifying existing settings)
        3. CREATE (creating new settings)
        4. QUERY (asking about settings)
        5. CHAT (default, when no keywords match)

        Args:
            user_input: User's natural language input

        Returns:
            Detected UserIntent
        """
        if not user_input:
            return self.default_intent

        input_lower = user_input.lower()

        # Check for keywords in priority order
        for intent in [UserIntent.SETTING, UserIntent.MODIFY,
                      UserIntent.CREATE, UserIntent.QUERY]:
            keywords = self.INTENT_KEYWORDS.get(intent, [])
            if any(keyword in input_lower for keyword in keywords):
                return intent

        # Default to CHAT if no keywords match
        return self.default_intent

    def recognize_setting_types(self, user_input: str) -> List[SettingType]:
        """
        Recognize which setting types are mentioned in the input.

        Checks for setting-type-specific keywords and returns all matching types.

        Args:
            user_input: User's natural language input

        Returns:
            List of involved SettingType (may be empty)
        """
        if not user_input:
            return []

        input_lower = user_input.lower()
        detected_types = []

        for setting_type, keywords in self.SETTING_TYPE_KEYWORDS.items():
            if any(keyword in input_lower for keyword in keywords):
                detected_types.append(setting_type)

        return detected_types

    def recognize(self, user_input: str) -> Tuple[UserIntent, List[SettingType]]:
        """
        Recognize both intent and setting types in one call.

        This is a convenience method that calls both recognize_intent()
        and recognize_setting_types().

        Args:
            user_input: User's natural language input

        Returns:
            Tuple of (UserIntent, List[SettingType])
        """
        intent = self.recognize_intent(user_input)
        setting_types = self.recognize_setting_types(user_input)

        return intent, setting_types

    def add_intent_keyword(self, intent: UserIntent, keyword: str) -> None:
        """
        Add a custom keyword for an intent.

        Args:
            intent: The intent to add the keyword to
            keyword: The keyword to add
        """
        if intent not in self.INTENT_KEYWORDS:
            self.INTENT_KEYWORDS[intent] = []
        if keyword not in self.INTENT_KEYWORDS[intent]:
            self.INTENT_KEYWORDS[intent].append(keyword.lower())

    def add_setting_type_keyword(self, setting_type: SettingType, keyword: str) -> None:
        """
        Add a custom keyword for a setting type.

        Args:
            setting_type: The setting type to add the keyword to
            keyword: The keyword to add
        """
        if setting_type not in self.SETTING_TYPE_KEYWORDS:
            self.SETTING_TYPE_KEYWORDS[setting_type] = []
        if keyword not in self.SETTING_TYPE_KEYWORDS[setting_type]:
            self.SETTING_TYPE_KEYWORDS[setting_type].append(keyword.lower())
