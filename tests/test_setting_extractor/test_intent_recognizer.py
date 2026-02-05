"""
Unit tests for intent recognizer.
"""

import pytest
from src.story.setting_extractor.intent_recognizer import (
    IntentRecognizer,
    KeywordIntentRecognizer
)
from src.story.setting_extractor.models import UserIntent, SettingType


class TestKeywordIntentRecognizer:
    """Test KeywordIntentRecognizer class."""

    def test_recognize_create_intent_chinese(self):
        """Test recognizing CREATE intent in Chinese."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("创建一个新角色") == UserIntent.CREATE
        assert recognizer.recognize_intent("添加新的设定") == UserIntent.CREATE
        assert recognizer.recognize_intent("开始写故事") == UserIntent.CREATE

    def test_recognize_create_intent_english(self):
        """Test recognizing CREATE intent in English."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("Create a new character") == UserIntent.CREATE
        assert recognizer.recognize_intent("Add a new setting") == UserIntent.CREATE
        assert recognizer.recognize_intent("Make a protagonist") == UserIntent.CREATE

    def test_recognize_modify_intent(self):
        """Test recognizing MODIFY intent."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("修改角色的性格") == UserIntent.MODIFY
        assert recognizer.recognize_intent("change the world setting") == UserIntent.MODIFY
        assert recognizer.recognize_intent("update the plot") == UserIntent.MODIFY

    def test_recognize_query_intent(self):
        """Test recognizing QUERY intent."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("角色叫什么名字?") == UserIntent.QUERY
        assert recognizer.recognize_intent("what is the world type?") == UserIntent.QUERY
        assert recognizer.recognize_intent("show me the plot") == UserIntent.QUERY

    def test_recognize_setting_intent(self):
        """Test recognizing SETTING intent."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("配置系统设置") == UserIntent.SETTING
        assert recognizer.recognize_intent("change the configuration") == UserIntent.SETTING
        assert recognizer.recognize_intent("settings") == UserIntent.SETTING

    def test_recognize_chat_intent(self):
        """Test recognizing CHAT intent (default)."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("hello") == UserIntent.CHAT
        assert recognizer.recognize_intent("how are you?") == UserIntent.CHAT
        assert recognizer.recognize_intent("随便聊聊") == UserIntent.CHAT

    def test_recognize_character_type(self):
        """Test recognizing character setting type."""
        recognizer = KeywordIntentRecognizer()

        types = recognizer.recognize_setting_types("创建一个角色")
        assert SettingType.CHARACTER in types

        types = recognizer.recognize_setting_types("The protagonist is brave")
        assert SettingType.CHARACTER in types

        types = recognizer.recognize_setting_types("他的性格很复杂")
        assert SettingType.CHARACTER in types

    def test_recognize_world_type(self):
        """Test recognizing world setting type."""
        recognizer = KeywordIntentRecognizer()

        types = recognizer.recognize_setting_types("这是一个奇幻世界")
        assert SettingType.WORLD in types

        types = recognizer.recognize_setting_types("The world has magic")
        assert SettingType.WORLD in types

        types = recognizer.recognize_setting_types("在这个时代")
        assert SettingType.WORLD in types

    def test_recognize_plot_type(self):
        """Test recognizing plot setting type."""
        recognizer = KeywordIntentRecognizer()

        types = recognizer.recognize_setting_types("故事的主要冲突是")
        assert SettingType.PLOT in types

        types = recognizer.recognize_setting_types("The plot has a twist")
        assert SettingType.PLOT in types

        types = recognizer.recognize_setting_types("剧情高潮是")
        assert SettingType.PLOT in types

    def test_recognize_style_type(self):
        """Test recognizing style setting type."""
        recognizer = KeywordIntentRecognizer()

        types = recognizer.recognize_setting_types("用第一人称写")
        assert SettingType.STYLE in types

        types = recognizer.recognize_setting_types("The tone is serious")
        assert SettingType.STYLE in types

        types = recognizer.recognize_setting_types("写作风格是")
        assert SettingType.STYLE in types

    def test_recognize_multiple_types(self):
        """Test recognizing multiple setting types."""
        recognizer = KeywordIntentRecognizer()

        types = recognizer.recognize_setting_types("创建一个角色，设定为奇幻世界")
        assert SettingType.CHARACTER in types
        assert SettingType.WORLD in types

    def test_recognize_combined(self):
        """Test the combined recognize method."""
        recognizer = KeywordIntentRecognizer()

        intent, types = recognizer.recognize("创建一个主角")

        assert intent == UserIntent.CREATE
        assert SettingType.CHARACTER in types

    def test_empty_input(self):
        """Test handling empty input."""
        recognizer = KeywordIntentRecognizer()

        assert recognizer.recognize_intent("") == UserIntent.CHAT
        assert recognizer.recognize_setting_types("") == []

    def test_custom_intent_keyword(self):
        """Test adding custom intent keywords."""
        recognizer = KeywordIntentRecognizer()

        # Add custom keyword for CREATE intent
        recognizer.add_intent_keyword(UserIntent.CREATE, "generate")

        assert recognizer.recognize_intent("Generate a character") == UserIntent.CREATE

    def test_custom_setting_type_keyword(self):
        """Test adding custom setting type keywords."""
        recognizer = KeywordIntentRecognizer()

        # Add custom keyword for CHARACTER type
        recognizer.add_setting_type_keyword(SettingType.CHARACTER, "hero")

        types = recognizer.recognize_setting_types("The hero is strong")
        assert SettingType.CHARACTER in types

    def test_priority_order(self):
        """Test that intent priority works correctly."""
        recognizer = KeywordIntentRecognizer()

        # SETTING should have priority over MODIFY
        assert recognizer.recognize_intent("配置修改") == UserIntent.SETTING

        # MODIFY should have priority over CREATE
        assert recognizer.recognize_intent("修改创建") == UserIntent.MODIFY
