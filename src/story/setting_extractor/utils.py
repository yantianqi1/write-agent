"""
Memory system integration for setting extractor.

This module provides utilities to integrate extracted settings with
the memory system for persistent storage and retrieval.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from .models import (
    ExtractedSettings, CharacterProfile, WorldSetting, PlotElement,
    StylePreference, SettingType
)

# Import memory system - assuming it exists in the project
# If not, we'll create a mock for now
try:
    from src.memory.base import MemoryLevel, BaseMemory
    from src.memory.impl import SemanticMemory
    MEMORY_SYSTEM_AVAILABLE = True
except ImportError:
    MEMORY_SYSTEM_AVAILABLE = False
    # Create mock classes for type hints
    class MemoryLevel:
        CHARACTER = "character"
        GLOBAL = "global"
        PLOT = "plot"
        STYLE = "style"

    class BaseMemory:
        pass


class MemorySystemIntegrator:
    """
    Integrates extracted settings with the memory system.

    This class handles converting extracted settings into memory
    entries and storing them at appropriate memory levels.
    """

    # Mapping of setting types to memory levels
    SETTING_TO_MEMORY_LEVEL = {
        SettingType.CHARACTER: MemoryLevel.CHARACTER if MEMORY_SYSTEM_AVAILABLE else "character",
        SettingType.WORLD: MemoryLevel.GLOBAL if MEMORY_SYSTEM_AVAILABLE else "global",
        SettingType.PLOT: MemoryLevel.PLOT if MEMORY_SYSTEM_AVAILABLE else "plot",
        SettingType.STYLE: MemoryLevel.STYLE if MEMORY_SYSTEM_AVAILABLE else "style"
    }

    def __init__(self, memory_system: Optional['BaseMemory'] = None):
        """
        Initialize the memory system integrator.

        Args:
            memory_system: Instance of the memory system. If None, uses default.
        """
        if not MEMORY_SYSTEM_AVAILABLE:
            print("Warning: Memory system not available. Settings will not be persisted.")
            self.memory_system = None
            return

        self.memory_system = memory_system

        # If no memory system provided, create a default one
        if self.memory_system is None:
            try:
                self.memory_system = SemanticMemory()
            except Exception as e:
                print(f"Warning: Could not initialize memory system: {e}")
                self.memory_system = None

    def save_settings(self,
                     settings: ExtractedSettings,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save extracted settings to the memory system.

        This method converts each setting type into appropriate
        memory entries and stores them.

        Args:
            settings: Extracted settings to save
            metadata: Optional metadata to attach to memory entries

        Returns:
            True if save was successful, False otherwise
        """
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            print("Memory system not available. Settings not saved.")
            return False

        try:
            # Save characters
            for character in settings.characters:
                self._save_character(character, metadata)

            # Save world setting
            if settings.world:
                self._save_world_setting(settings.world, metadata)

            # Save plot elements
            if settings.plot:
                self._save_plot_element(settings.plot, metadata)

            # Save style preferences
            if settings.style:
                self._save_style_preference(settings.style, metadata)

            return True

        except Exception as e:
            print(f"Error saving settings to memory: {e}")
            return False

    def _save_character(self,
                       character: CharacterProfile,
                       metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save a character profile to memory."""
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            return

        # Create memory content
        content = self._character_to_memory_content(character)

        # Create metadata
        entry_metadata = {
            "setting_type": SettingType.CHARACTER.value,
            "timestamp": datetime.now().isoformat(),
            "character_name": character.name or "Unnamed"
        }

        if metadata:
            entry_metadata.update(metadata)

        # Store in memory system
        # Note: Adapt this to your actual memory system API
        try:
            # Example: self.memory_system.add(
            #     content=content,
            #     level=MemoryLevel.CHARACTER,
            #     metadata=entry_metadata
            # )
            print(f"Would save character: {character.name or 'Unnamed'}")
            print(f"Content: {content}")
        except Exception as e:
            print(f"Error saving character: {e}")

    def _save_world_setting(self,
                           world: WorldSetting,
                           metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save world setting to memory."""
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            return

        content = self._world_to_memory_content(world)

        entry_metadata = {
            "setting_type": SettingType.WORLD.value,
            "timestamp": datetime.now().isoformat(),
            "world_type": world.world_type or "Unknown"
        }

        if metadata:
            entry_metadata.update(metadata)

        try:
            # Example: self.memory_system.add(
            #     content=content,
            #     level=MemoryLevel.GLOBAL,
            #     metadata=entry_metadata
            # )
            print(f"Would save world setting: {world.world_type or 'Unknown'}")
            print(f"Content: {content}")
        except Exception as e:
            print(f"Error saving world setting: {e}")

    def _save_plot_element(self,
                          plot: PlotElement,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save plot elements to memory."""
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            return

        content = self._plot_to_memory_content(plot)

        entry_metadata = {
            "setting_type": SettingType.PLOT.value,
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            entry_metadata.update(metadata)

        try:
            # Example: self.memory_system.add(
            #     content=content,
            #     level=MemoryLevel.PLOT,
            #     metadata=entry_metadata
            # )
            print("Would save plot elements")
            print(f"Content: {content}")
        except Exception as e:
            print(f"Error saving plot elements: {e}")

    def _save_style_preference(self,
                              style: StylePreference,
                              metadata: Optional[Dict[str, Any]] = None) -> None:
        """Save style preferences to memory."""
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            return

        content = self._style_to_memory_content(style)

        entry_metadata = {
            "setting_type": SettingType.STYLE.value,
            "timestamp": datetime.now().isoformat()
        }

        if metadata:
            entry_metadata.update(metadata)

        try:
            # Example: self.memory_system.add(
            #     content=content,
            #     level=MemoryLevel.STYLE,
            #     metadata=entry_metadata
            # )
            print("Would save style preferences")
            print(f"Content: {content}")
        except Exception as e:
            print(f"Error saving style preferences: {e}")

    def load_settings(self) -> Optional[ExtractedSettings]:
        """
        Load settings from the memory system.

        Returns:
            ExtractedSettings if successful, None otherwise
        """
        if not MEMORY_SYSTEM_AVAILABLE or self.memory_system is None:
            print("Memory system not available. Cannot load settings.")
            return None

        try:
            # Load characters
            characters = self._load_characters()

            # Load world
            world = self._load_world_setting()

            # Load plot
            plot = self._load_plot_element()

            # Load style
            style = self._load_style_preference()

            return ExtractedSettings(
                characters=characters,
                world=world,
                plot=plot,
                style=style
            )

        except Exception as e:
            print(f"Error loading settings from memory: {e}")
            return None

    def _load_characters(self) -> List[CharacterProfile]:
        """Load characters from memory."""
        # Implement actual loading logic based on your memory system
        return []

    def _load_world_setting(self) -> Optional[WorldSetting]:
        """Load world setting from memory."""
        # Implement actual loading logic based on your memory system
        return None

    def _load_plot_element(self) -> Optional[PlotElement]:
        """Load plot elements from memory."""
        # Implement actual loading logic based on your memory system
        return None

    def _load_style_preference(self) -> Optional[StylePreference]:
        """Load style preferences from memory."""
        # Implement actual loading logic based on your memory system
        return None

    # Content formatters

    def _character_to_memory_content(self, character: CharacterProfile) -> str:
        """Convert character profile to memory content string."""
        parts = []

        if character.name:
            parts.append(f"Name: {character.name}")

        if character.role:
            parts.append(f"Role: {character.role}")

        if character.personality:
            parts.append(f"Personality: {character.personality}")

        if character.background:
            parts.append(f"Background: {character.background}")

        if character.appearance:
            parts.append(f"Appearance: {character.appearance}")

        if character.age:
            parts.append(f"Age: {character.age}")

        if character.abilities:
            parts.append(f"Abilities: {', '.join(character.abilities)}")

        if character.relationships:
            parts.append(f"Relationships: {', '.join(character.relationships)}")

        return "\n".join(parts) if parts else "Character profile (no details)"

    def _world_to_memory_content(self, world: WorldSetting) -> str:
        """Convert world setting to memory content string."""
        parts = []

        if world.world_type:
            parts.append(f"Type: {world.world_type}")

        if world.era:
            parts.append(f"Era: {world.era}")

        if world.magic_system:
            parts.append(f"Magic System: {world.magic_system}")

        if world.technology_level:
            parts.append(f"Technology: {world.technology_level}")

        if world.geography:
            parts.append(f"Geography: {world.geography}")

        if world.locations:
            parts.append(f"Locations: {', '.join(world.locations)}")

        if world.rules:
            parts.append(f"Rules: {', '.join(world.rules)}")

        if world.factions:
            parts.append(f"Factions: {', '.join(world.factions)}")

        return "\n".join(parts) if parts else "World setting (no details)"

    def _plot_to_memory_content(self, plot: PlotElement) -> str:
        """Convert plot elements to memory content string."""
        parts = []

        if plot.inciting_incident:
            parts.append(f"Inciting Incident: {plot.inciting_incident}")

        if plot.conflict:
            parts.append(f"Conflict: {plot.conflict}")

        if plot.climax:
            parts.append(f"Climax: {plot.climax}")

        if plot.resolution:
            parts.append(f"Resolution: {plot.resolution}")

        if plot.themes:
            parts.append(f"Themes: {', '.join(plot.themes)}")

        if plot.rising_action:
            parts.append(f"Rising Action: {', '.join(plot.rising_action)}")

        if plot.subplot_points:
            parts.append(f"Subplots: {', '.join(plot.subplot_points)}")

        return "\n".join(parts) if parts else "Plot elements (no details)"

    def _style_to_memory_content(self, style: StylePreference) -> str:
        """Convert style preferences to memory content string."""
        parts = []

        if style.writing_style:
            parts.append(f"Writing Style: {style.writing_style}")

        if style.pov:
            parts.append(f"POV: {style.pov}")

        if style.tone:
            parts.append(f"Tone: {style.tone}")

        if style.pacing:
            parts.append(f"Pacing: {style.pacing}")

        if style.tense:
            parts.append(f"Tense: {style.tense}")

        if style.genre:
            parts.append(f"Genre: {', '.join(style.genre)}")

        return "\n".join(parts) if parts else "Style preferences (no details)"
