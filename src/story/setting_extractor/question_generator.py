"""
Question generation for collecting missing setting information.

This module provides functionality to generate intelligent follow-up
questions to collect missing information from users.
"""

from abc import ABC, abstractmethod
from typing import List
import random
from .models import MissingInfo, ExtractedSettings


class QuestionGenerator(ABC):
    """
    Abstract base class for question generators.

    Question generators analyze missing information and create
    engaging follow-up questions to collect complete settings.
    """

    @abstractmethod
    def generate_questions(self,
                          settings: ExtractedSettings,
                          missing_info: List[MissingInfo],
                          count: int = 3) -> List[str]:
        """
        Generate follow-up questions based on missing information.

        Args:
            settings: Current extracted settings
            missing_info: List of missing information
            count: Maximum number of questions to generate

        Returns:
            List of follow-up questions (strings)
        """
        pass


class PriorityQuestionGenerator(QuestionGenerator):
    """
    Question generator that prioritizes by missing info priority.

    This generator selects the most important missing information
    and generates diverse questions to collect it.
    """

    # Question variations for different contexts
    OPENING_PHRASES = [
        "Could you tell me",
        "I'd like to know",
        "Can you describe",
        "What about",
        "Let's explore"
    ]

    CLOSING_PHRASES = [
        "This will help create a more detailed story.",
        "This information will be useful for the plot.",
        "This adds depth to the setting.",
        "This helps shape the narrative.",
        "This enriches the story world."
    ]

    def __init__(self, diversity_factor: float = 0.3):
        """
        Initialize the priority question generator.

        Args:
            diversity_factor: How much to randomize question selection (0.0-1.0)
                             Higher = more diversity, Lower = more priority-focused
        """
        self.diversity_factor = diversity_factor

    def generate_questions(self,
                          settings: ExtractedSettings,
                          missing_info: List[MissingInfo],
                          count: int = 3) -> List[str]:
        """
        Generate follow-up questions based on missing information.

        This method selects the most important missing information
        and generates engaging questions.

        Args:
            settings: Current extracted settings
            missing_info: List of missing information (should be pre-sorted by priority)
            count: Maximum number of questions to generate (default: 3)

        Returns:
            List of follow-up questions (strings)
        """
        if not missing_info:
            # No missing info, return completion message
            return ["All the essential information has been collected!"]

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
