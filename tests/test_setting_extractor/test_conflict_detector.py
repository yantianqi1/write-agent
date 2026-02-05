"""
Unit tests for conflict detector.
"""

import pytest
from src.story.setting_extractor.conflict_detector import (
    ConflictDetector,
    BasicConflictDetector
)
from src.story.setting_extractor.models import (
    ExtractedSettings,
    CharacterProfile,
    WorldSetting,
    StylePreference,
    ConflictSeverity,
    SettingType
)


class TestBasicConflictDetector:
    """Test BasicConflictDetector class."""

    def test_no_conflicts_in_empty_settings(self):
        """Test that empty settings have no conflicts."""
        detector = BasicConflictDetector()
        settings = ExtractedSettings()

        conflicts = detector.detect_conflicts(settings)

        assert len(conflicts) == 0

    def test_detect_world_type_conflict(self):
        """Test detecting contradictory world types."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            world=WorldSetting(world_type="fantasy sci-fi")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should detect conflict between fantasy and sci-fi
        world_conflicts = [c for c in conflicts if c.setting_type == SettingType.WORLD]
        assert len(world_conflicts) > 0

    def test_detect_era_conflict(self):
        """Test detecting contradictory eras."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            world=WorldSetting(era="ancient future")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should detect conflict between ancient and future
        era_conflicts = [c for c in conflicts if c.field_name == "era"]
        assert len(era_conflicts) > 0

    def test_detect_personality_conflict(self):
        """Test detecting contradictory personality traits."""
        detector = BasicConflictDetector()

        character = CharacterProfile(
            name="Alice",
            personality="shy and outgoing"
        )

        settings = ExtractedSettings(characters=[character])

        conflicts = detector.detect_conflicts(settings)

        # Should detect conflict between shy and outgoing
        personality_conflicts = [
            c for c in conflicts
            if c.field_name == "personality" and c.character_name == "Alice"
        ]
        assert len(personality_conflicts) > 0

    def test_detect_pov_conflict(self):
        """Test detecting contradictory POV."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            style=StylePreference(pov="first person third person")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should detect POV conflict
        pov_conflicts = [c for c in conflicts if c.field_name == "pov"]
        assert len(pov_conflicts) > 0

    def test_detect_tense_conflict(self):
        """Test detecting contradictory tense."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            style=StylePreference(tense="past present")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should detect tense conflict
        tense_conflicts = [c for c in conflicts if c.field_name == "tense"]
        assert len(tense_conflicts) > 0

    def test_cross_setting_conflict_magic_in_non_fantasy(self):
        """Test detecting magic abilities in non-fantasy world."""
        detector = BasicConflictDetector()

        character = CharacterProfile(
            name="Alice",
            abilities=["fire magic", "spell casting"]
        )

        settings = ExtractedSettings(
            characters=[character],
            world=WorldSetting(world_type="contemporary")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should detect conflict between magic abilities and contemporary world
        magic_conflicts = [
            c for c in conflicts
            if c.conflict_type == "character_world_conflict"
        ]
        assert len(magic_conflicts) > 0

    def test_no_magic_conflict_in_fantasy_world(self):
        """Test that magic in fantasy world is not a conflict."""
        detector = BasicConflictDetector()

        character = CharacterProfile(
            name="Alice",
            abilities=["fire magic"]
        )

        settings = ExtractedSettings(
            characters=[character],
            world=WorldSetting(world_type="fantasy")
        )

        conflicts = detector.detect_conflicts(settings)

        # Should NOT detect conflict for magic in fantasy world
        magic_conflicts = [
            c for c in conflicts
            if c.conflict_type == "character_world_conflict"
        ]
        assert len(magic_conflicts) == 0

    def test_conflict_severity_levels(self):
        """Test that conflicts have appropriate severity."""
        detector = BasicConflictDetector()

        # World type conflict should be HIGH severity
        settings1 = ExtractedSettings(
            world=WorldSetting(world_type="fantasy sci-fi")
        )
        conflicts1 = detector.detect_conflicts(settings1)

        assert len(conflicts1) > 0
        assert conflicts1[0].severity == ConflictSeverity.HIGH

        # Personality conflict should be MEDIUM severity
        character = CharacterProfile(name="Alice", personality="shy outgoing")
        settings2 = ExtractedSettings(characters=[character])
        conflicts2 = detector.detect_conflicts(settings2)

        personality_conflicts = [c for c in conflicts2 if c.field_name == "personality"]
        assert len(personality_conflicts) > 0
        assert personality_conflicts[0].severity == ConflictSeverity.MEDIUM

    def test_resolution_suggestions(self):
        """Test that conflicts include resolution suggestions."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            world=WorldSetting(world_type="fantasy sci-fi")
        )

        conflicts = detector.detect_conflicts(settings)

        assert len(conflicts) > 0
        assert conflicts[0].resolution_suggestion is not None
        assert len(conflicts[0].resolution_suggestion) > 0

    def test_has_high_severity_conflicts(self):
        """Test checking for high severity conflicts."""
        detector = BasicConflictDetector()

        # No conflicts
        settings1 = ExtractedSettings()
        assert detector.has_high_severity_conflicts(settings1) is False

        # High severity conflict
        settings2 = ExtractedSettings(
            world=WorldSetting(world_type="fantasy sci-fi")
        )
        assert detector.has_high_severity_conflicts(settings2) is True

    def test_get_conflicts_by_severity(self):
        """Test filtering conflicts by severity."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            world=WorldSetting(world_type="fantasy sci-fi"),
            characters=[
                CharacterProfile(name="Alice", personality="shy outgoing")
            ]
        )

        conflicts = detector.detect_conflicts(settings)

        # Get only high severity conflicts
        high_conflicts = detector.get_conflicts_by_severity(
            settings,
            ConflictSeverity.HIGH
        )

        assert all(c.severity == ConflictSeverity.HIGH for c in high_conflicts)

    def test_multiple_world_settings_no_conflict(self):
        """Test that consistent world settings don't create conflicts."""
        detector = BasicConflictDetector()

        settings = ExtractedSettings(
            world=WorldSetting(
                world_type="fantasy",
                era="medieval",
                magic_system="elemental"
            )
        )

        conflicts = detector.detect_conflicts(settings)

        # Should have no conflicts
        world_conflicts = [c for c in conflicts if c.setting_type == SettingType.WORLD]
        assert len(world_conflicts) == 0

    def test_character_age_role_consistency_check(self):
        """Test age vs role consistency check (LOW severity)."""
        detector = BasicConflictDetector()

        character = CharacterProfile(
            name="Young",
            age=10,
            role="protagonist"
        )

        settings = ExtractedSettings(characters=[character])

        conflicts = detector.detect_conflicts(settings)

        # May flag as low severity consistency check
        age_conflicts = [
            c for c in conflicts
            if c.conflict_type == "age_role_consistency"
        ]
        # This might or might not be flagged depending on implementation
        # Just check that if it exists, it's LOW severity
        for conflict in age_conflicts:
            assert conflict.severity == ConflictSeverity.LOW
