"""
Prompt generation for AI setting completion (INTERNAL USE).

This module provides functionality to generate internal prompts for
AI to auto-complete missing settings. Users never see these prompts.

IMPLICIT MODE: This is for AI internal use only, not for user interaction.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
from dataclasses import dataclass
import random
from .models import MissingInfo, ExtractedSettings, SettingType


@dataclass
class CompletionPrompt:
    """Internal prompt for AI setting completion."""
    setting_type: str
    field_name: str
    completion_instruction: str
    context_hints: List[str]
    default_template: str


class PromptGenerator(ABC):
    """
    Abstract base class for internal prompt generators.

    Prompt generators create instructions for AI to auto-complete
    missing settings. These are INTERNAL prompts, never shown to users.
    """

    @abstractmethod
    def generate_completion_prompts(self,
                                   settings: ExtractedSettings,
                                   completion_tasks: Dict[str, List[str]],
                                   count: int = 10) -> List[CompletionPrompt]:
        """
        Generate internal completion prompts.

        Args:
            settings: Current extracted settings
            completion_tasks: Dictionary of tasks per setting type
            count: Maximum number of prompts to generate

        Returns:
            List of CompletionPrompt for AI to process
        """
        pass


class InternalPromptGenerator(PromptGenerator):
    """
    Internal prompt generator for AI auto-completion.

    This generator creates detailed instructions for AI to
    intelligently fill in missing setting information.
    """

    # Completion instructions by setting type and field
    CHARACTER_INSTRUCTIONS = {
        "name": "Generate a fitting name for the character based on story context",
        "role": "Infer or assign a narrative role (protagonist, antagonist, supporting)",
        "personality": "Create a personality that fits the story genre and character role",
        "background": "Generate a backstory that explains the character's motivations",
        "appearance": "Create physical appearance that reflects their personality",
        "abilities": "Give abilities/skills appropriate for the world type and character role",
        "relationships": "Define relationships that create story conflict and depth"
    }

    WORLD_INSTRUCTIONS = {
        "world_type": "Infer from story description or default to contemporary",
        "era": "Match era to world type (future for sci-fi, past for fantasy/historical)",
        "geography": "Create key locations relevant to the plot",
        "magic_system": "Design magic/ability system consistent with world type",
        "technology_level": "Set technology level appropriate for world type",
        "rules": "Define world rules that create interesting constraints",
        "factions": "Create factions that generate conflict and political intrigue"
    }

    PLOT_INSTRUCTIONS = {
        "inciting_incident": "Create an event that disrupts the protagonist's normal life",
        "conflict": "Design a central conflict that forces character growth",
        "climax": "Plan a climactic confrontation that resolves the main conflict",
        "resolution": "Create a satisfying resolution that shows character change",
        "themes": "Infer themes from the story concept and character arcs",
        "rising_action": "Design plot points that escalate tension toward climax"
    }

    STYLE_INSTRUCTIONS = {
        "pov": "Default to third person limited unless first person fits the story better",
        "writing_style": "Match writing style to genre and tone",
        "tone": "Infer from story description (humor for light concepts, serious for dark)",
        "pacing": "Set pacing appropriate for genre (fast for action, slow for drama)",
        "tense": "Default to past tense, use present tense for immediacy"
    }

    def __init__(self, diversity_factor: float = 0.3):
        """
        Initialize the internal prompt generator.

        Args:
            diversity_factor: How much to diversify completion (0.0-1.0)
        """
        self.diversity_factor = diversity_factor

    def generate_completion_prompts(self,
                                   settings: ExtractedSettings,
                                   completion_tasks: Dict[str, List[str]],
                                   count: int = 10) -> List[CompletionPrompt]:
        """
        Generate internal completion prompts for AI.

        Args:
            settings: Current extracted settings
            completion_tasks: Dictionary of tasks per setting type
            count: Maximum number of prompts to generate

        Returns:
            List of CompletionPrompt for AI processing
        """
        prompts = []

        # Generate prompts for each setting type
        for setting_type, fields in completion_tasks.items():
            if not fields:
                continue

            setting_prompts = self._generate_prompts_for_type(
                setting_type, fields, settings, count
            )
            prompts.extend(setting_prompts)

        return prompts[:count]

    def _generate_prompts_for_type(self,
                                   setting_type: str,
                                   fields: List[str],
                                   settings: ExtractedSettings,
                                   count: int) -> List[CompletionPrompt]:
        """Generate prompts for a specific setting type."""
        prompts = []

        for field in fields:
            instruction = self._get_instruction(setting_type, field)
            context_hints = self._get_context_hints(setting_type, field, settings)
            default_template = self._get_default_template(setting_type, field)

            prompts.append(CompletionPrompt(
                setting_type=setting_type,
                field_name=field,
                completion_instruction=instruction,
                context_hints=context_hints,
                default_template=default_template
            ))

        return prompts

    def _get_instruction(self, setting_type: str, field: str) -> str:
        """Get completion instruction for a field."""
        instructions = {
            "character": self.CHARACTER_INSTRUCTIONS,
            "world": self.WORLD_INSTRUCTIONS,
            "plot": self.PLOT_INSTRUCTIONS,
            "style": self.STYLE_INSTRUCTIONS
        }
        return instructions.get(setting_type, {}).get(
            field,
            f"Generate appropriate {field} based on story context"
        )

    def _get_context_hints(self, setting_type: str,
                          field: str,
                          settings: ExtractedSettings) -> List[str]:
        """Get context hints for completion."""
        hints = []

        # Add world type context
        if settings.world and settings.world.world_type:
            hints.append(f"World type: {settings.world.world_type}")

        # Add plot context
        if settings.plot and settings.plot.conflict:
            hints.append(f"Main conflict: {settings.plot.conflict}")

        # Add character context for non-character fields
        if setting_type != "character" and settings.characters:
            main_char = settings.characters[0] if settings.characters else None
            if main_char:
                char_desc = f"Main character: {main_char.name or 'Unnamed'}"
                if main_char.role:
                    char_desc += f" ({main_char.role})"
                if main_char.personality:
                    char_desc += f" - {main_char.personality}"
                hints.append(char_desc)

        return hints

    def _get_default_template(self, setting_type: str, field: str) -> str:
        """Get default value template."""
        templates = {
            ("character", "name"): "Generate a name fitting the world type",
            ("character", "personality"): "Brave, kind, and growing",
            ("character", "role"): "Protagonist",
            ("character", "background"): "An ordinary person facing extraordinary circumstances",
            ("world", "world_type"): "Contemporary",
            ("world", "era"): "21st century",
            ("plot", "conflict"): "The protagonist must overcome a significant challenge",
            ("plot", "inciting_incident"): "An unexpected event changes everything",
            ("style", "pov"): "Third person limited",
            ("style", "tense"): "Past tense",
            ("style", "tone"): "Balanced",
            ("style", "pacing"): "Medium"
        }
        return templates.get((setting_type, field), "Use sensible default")


# Backward compatibility - keep old class name but redirect to new behavior
class QuestionGenerator(PromptGenerator):
    """
    DEPRECATED: Use PromptGenerator instead.

    This class is kept for backward compatibility but now
    generates internal prompts instead of user questions.
    """

    def __init__(self, internal_mode: bool = True):
        """
        Initialize (deprecated wrapper).

        Args:
            internal_mode: Must be True (forwarding to PromptGenerator)
        """
        self._internal = InternalPromptGenerator()

    def generate_questions(self,
                          settings: ExtractedSettings,
                          missing_info: List[MissingInfo],
                          count: int = 3) -> List[str]:
        """
        DEPRECATED: Use generate_completion_prompts instead.

        This method now returns internal completion instructions
        rather than user-facing questions.
        """
        # Convert missing_info to completion_tasks format
        completion_tasks = {
            "character": [],
            "world": [],
            "plot": [],
            "style": []
        }

        for info in missing_info:
            setting_type = info.setting_type.value
            if setting_type in completion_tasks:
                completion_tasks[setting_type].append(info.field_name)

        prompts = self._internal.generate_completion_prompts(
            settings, completion_tasks, count
        )

        # Return as instruction strings (for backward compat)
        return [p.completion_instruction for p in prompts]


class PriorityQuestionGenerator(QuestionGenerator):
    """
    DEPRECATED: Use InternalPromptGenerator instead.

    This class is kept for backward compatibility.
    """

    def __init__(self, diversity_factor: float = 0.3):
        """
        Initialize (deprecated wrapper).

        Args:
            diversity_factor: Passed to InternalPromptGenerator
        """
        self._internal = InternalPromptGenerator(diversity_factor)

    def generate_questions(self,
                          settings: ExtractedSettings,
                          missing_info: List[MissingInfo],
                          count: int = 3) -> List[str]:
        """Generate questions (deprecated - redirects to internal prompts)."""
        # Convert to completion tasks
        completion_tasks = {
            "character": [],
            "world": [],
            "plot": [],
            "style": []
        }

        for info in missing_info[:count]:
            setting_type = info.setting_type.value
            if setting_type in completion_tasks:
                completion_tasks[setting_type].append(info.field_name)

        prompts = self._internal.generate_completion_prompts(
            settings, completion_tasks, count
        )

        return [p.completion_instruction for p in prompts]

        # Select which missing info to ask about
        selected = self._select_missing_info(missing_info, count)

        # Generate questions for selected items
        questions = []
        for item in selected:
            question = self._generate_question_for_item(item, settings)
            if question:
                questions.append(question)

        return questions

    def _select_missing_info(self,
                            missing_info: List[MissingInfo],
                            count: int) -> List[MissingInfo]:
        """
        Select which missing information items to ask about.

        Strategy: Mix of priority-based selection and diversity.

        Args:
            missing_info: List of missing information (pre-sorted by priority)
            count: Number of items to select

        Returns:
            Selected MissingInfo items
        """
        if len(missing_info) <= count:
            return missing_info

        # Determine how many to pick from top priority vs diverse selection
        priority_count = int(count * (1.0 - self.diversity_factor))
        diversity_count = count - priority_count

        selected = []

        # Pick top priority items
        selected.extend(missing_info[:priority_count])

        # Pick diverse items from remaining
        remaining = missing_info[priority_count:]
        if remaining and diversity_count > 0:
            # Try to pick diverse setting types
            selected_types = {item.setting_type for item in selected}

            for item in remaining:
                if len(selected) >= count:
                    break

                # Prioritize items from different setting types
                if item.setting_type not in selected_types:
                    selected.append(item)
                    selected_types.add(item.setting_type)

            # If still need more, pick from remaining
            while len(selected) < count and len(remaining) > len(selected):
                for item in remaining:
                    if item not in selected:
                        selected.append(item)
                        break

        return selected[:count]

    def _generate_question_for_item(self,
                                   item: MissingInfo,
                                   settings: ExtractedSettings) -> str:
        """
        Generate a specific question for a missing info item.

        Args:
            item: The missing information item
            settings: Current settings (for context)

        Returns:
            Generated question string
        """
        # Start with the suggested question from the missing info
        base_question = item.suggested_question

        # Add variety based on setting type
        if item.setting_type.value == "character":
            return self._generate_character_question(item, settings)
        elif item.setting_type.value == "world":
            return self._generate_world_question(item, settings)
        elif item.setting_type.value == "plot":
            return self._generate_plot_question(item, settings)
        elif item.setting_type.value == "style":
            return self._generate_style_question(item, settings)
        else:
            return base_question

    def _generate_character_question(self,
                                    item: MissingInfo,
                                    settings: ExtractedSettings) -> str:
        """Generate a character-related question."""
        character_name = item.character_name or "your character"

        if item.field_name == "name":
            variations = [
                f"What shall we name {character_name}?",
                f"What's a good name for {character_name}?",
                f"Please provide a name for {character_name}."
            ]
        elif item.field_name == "role":
            variations = [
                f"What role does {character_name} play in the story?",
                f"Is {character_name} a protagonist, antagonist, or supporting character?",
                f"Tell me about {character_name}'s role in the narrative."
            ]
        elif item.field_name == "personality":
            variations = [
                f"How would you describe {character_name}'s personality?",
                f"What traits define {character_name}'s character?",
                f"What makes {character_name} unique?"
            ]
        elif item.field_name == "background":
            variations = [
                f"What's {character_name}'s backstory?",
                f"Tell me about {character_name}'s past and history.",
                f"What events shaped {character_name} into who they are?"
            ]
        elif item.field_name == "appearance":
            variations = [
                f"What does {character_name} look like?",
                f"Describe {character_name}'s physical appearance.",
                f"What are {character_name}'s distinguishing features?"
            ]
        elif item.field_name == "abilities":
            variations = [
                f"What special abilities or skills does {character_name} have?",
                f"What is {character_name} good at?",
                f"Does {character_name} have any unique powers or talents?"
            ]
        elif item.field_name == "relationships":
            variations = [
                f"Who are the important people in {character_name}'s life?",
                f"Tell me about {character_name}'s relationships.",
                f"Does {character_name} have friends, family, or rivals?"
            ]
        else:
            variations = [item.suggested_question]

        return random.choice(variations)

    def _generate_world_question(self,
                                 item: MissingInfo,
                                 settings: ExtractedSettings) -> str:
        """Generate a world-related question."""
        if item.field_name == "world_type":
            variations = [
                "What kind of world is your story set in? (fantasy, sci-fi, contemporary, historical, etc.)",
                "Describe the world where your story takes place.",
                "What's the setting of your story like?"
            ]
        elif item.field_name == "era":
            variations = [
                "What time period is your story set in?",
                "When does your story take place?",
                "What era or timeline does your story follow?"
            ]
        elif item.field_name == "geography":
            variations = [
                "What are the important locations in your story world?",
                "Describe the geography and key places in your setting.",
                "Where do the events of the story take place?"
            ]
        elif item.field_name == "magic_system":
            variations = [
                "How does magic work in your world?",
                "Tell me about the magic system or supernatural elements.",
                "What are the rules governing magic in this world?"
            ]
        elif item.field_name == "technology_level":
            variations = [
                "What's the technology level in this world?",
                "How advanced is technology in your setting?",
                "Describe the technological aspects of your world."
            ]
        elif item.field_name == "rules":
            variations = [
                "What are the important rules that govern this world?",
                "Are there any special laws or rules in this setting?",
                "What makes this world unique in terms of its rules?"
            ]
        elif item.field_name == "factions":
            variations = [
                "What are the major factions or groups in this world?",
                "Tell me about the political or social groups in your setting.",
                "Who are the key players in this world?"
            ]
        else:
            variations = [item.suggested_question]

        return random.choice(variations)

    def _generate_plot_question(self,
                               item: MissingInfo,
                               settings: ExtractedSettings) -> str:
        """Generate a plot-related question."""
        if item.field_name == "inciting_incident":
            variations = [
                "What event starts your story?",
                "What's the inciting incident that sets everything in motion?",
                "How does the story begin?"
            ]
        elif item.field_name == "conflict":
            variations = [
                "What's the main conflict in your story?",
                "What drives the story forward?",
                "What's the central problem or struggle?"
            ]
        elif item.field_name == "climax":
            variations = [
                "What's the climactic moment of your story?",
                "How does the story reach its peak?",
                "What's the most intense moment in the narrative?"
            ]
        elif item.field_name == "resolution":
            variations = [
                "How does your story end?",
                "What's the resolution of the conflict?",
                "How are things resolved at the end?"
            ]
        elif item.field_name == "themes":
            variations = [
                "What are the main themes of your story?",
                "What ideas or messages do you want to explore?",
                "What's the deeper meaning behind the story?"
            ]
        elif item.field_name == "rising_action":
            variations = [
                "What key events lead up to the climax?",
                "What happens between the beginning and the climax?",
                "Describe the major plot developments."
            ]
        else:
            variations = [item.suggested_question]

        return random.choice(variations)

    def _generate_style_question(self,
                                item: MissingInfo,
                                settings: ExtractedSettings) -> str:
        """Generate a style-related question."""
        if item.field_name == "pov":
            variations = [
                "What point of view should the story use? (first person, third person limited, third person omniscient)",
                "Who's telling the story?",
                "Should we see the story through one character's eyes or multiple perspectives?"
            ]
        elif item.field_name == "writing_style":
            variations = [
                "What writing style do you prefer? (formal, casual, poetic, straightforward)",
                "How should the story be written?",
                "Describe your preferred writing style."
            ]
        elif item.field_name == "tone":
            variations = [
                "What tone should the story have? (serious, humorous, dark, light-hearted)",
                "What's the emotional tone of the story?",
                "Should the story feel serious, funny, dark, or uplifting?"
            ]
        elif item.field_name == "pacing":
            variations = [
                "What pacing do you prefer? (fast-paced, moderate, slow and detailed)",
                "How quickly should the story move?",
                "Should the story be fast-paced or more leisurely?"
            ]
        elif item.field_name == "tense":
            variations = [
                "What tense should the story be written in? (past tense, present tense)",
                "Should the story be written in past or present tense?",
                "Do you prefer 'was' or 'is'?"
            ]
        else:
            variations = [item.suggested_question]

        return random.choice(variations)
