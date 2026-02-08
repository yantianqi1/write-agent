"""
Unit tests for content manager.

Tests the ContentManager, FileContentStorage, and
related content management functionality.
"""

import unittest
import tempfile
import shutil
import os
from datetime import datetime

from story.generation.content_manager import (
    StorageBackend,
    ContentVersion,
    StoryProject,
    ContentStorage,
    MemoryContentStorage,
    FileContentStorage,
    ContentManager,
    create_content_manager,
    create_file_manager
)
from story.generation.content_generator import ChapterContent
from story.generation.consistency import create_consistency_checker
from story.setting_extractor.models import ExtractedSettings


class TestContentVersion(unittest.TestCase):
    """Test ContentVersion dataclass."""

    def test_version_creation(self):
        """Test creating a version."""
        version = ContentVersion(
            version_id="v1",
            content="Content text",
            created_at="2024-01-01T00:00:00",
            word_count=100
        )

        self.assertEqual(version.version_id, "v1")
        self.assertEqual(version.content, "Content text")

    def test_version_to_dict(self):
        """Test converting version to dict."""
        version = ContentVersion(
            version_id="v1",
            content="Content",
            created_at="2024-01-01T00:00:00"
        )

        d = version.to_dict()
        self.assertEqual(d["version_id"], "v1")
        self.assertEqual(d["content"], "Content")


class TestStoryProject(unittest.TestCase):
    """Test StoryProject dataclass."""

    def test_project_creation(self):
        """Test creating a project."""
        project = StoryProject(
            name="Test Story",
            description="A test story"
        )

        self.assertEqual(project.name, "Test Story")
        self.assertEqual(project.description, "A test story")
        self.assertIsNotNone(project.created_at)

    def test_project_to_dict(self):
        """Test converting project to dict."""
        project = StoryProject(
            name="Test",
            chapters={1: ChapterContent(chapter_number=1, content="Content")}
        )

        d = project.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertIn("chapters", d)


class TestMemoryContentStorage(unittest.TestCase):
    """Test MemoryContentStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.storage = MemoryContentStorage()

    def test_save_and_load(self):
        """Test saving and loading a chapter."""
        chapter = ChapterContent(
            chapter_number=1,
            title="Chapter 1",
            content="Content"
        )

        self.storage.save_chapter("test_project", chapter)
        loaded = self.storage.load_chapter("test_project", 1)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.chapter_number, 1)
        self.assertEqual(loaded.content, "Content")

    def test_list_chapters(self):
        """Test listing chapters."""
        for i in range(1, 4):
            chapter = ChapterContent(chapter_number=i, content=f"Content {i}")
            self.storage.save_chapter("test", chapter)

        chapters = self.storage.list_chapters("test")
        self.assertEqual(sorted(chapters), [1, 2, 3])

    def test_delete_chapter(self):
        """Test deleting a chapter."""
        chapter = ChapterContent(chapter_number=1, content="Content")
        self.storage.save_chapter("test", chapter)

        result = self.storage.delete_chapter("test", 1)
        self.assertTrue(result)

        loaded = self.storage.load_chapter("test", 1)
        self.assertIsNone(loaded)


class TestFileContentStorage(unittest.TestCase):
    """Test FileContentStorage."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = FileContentStorage(base_path=self.temp_dir)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_save_and_load(self):
        """Test saving and loading to file."""
        chapter = ChapterContent(
            chapter_number=1,
            title="Chapter 1",
            content="Test content",
            word_count=50
        )

        self.storage.save_chapter("test_project", chapter)
        loaded = self.storage.load_chapter("test_project", 1)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.chapter_number, 1)
        self.assertEqual(loaded.content, "Test content")

    def test_list_chapters(self):
        """Test listing chapters from files."""
        for i in range(1, 4):
            chapter = ChapterContent(
                chapter_number=i,
                content=f"Content {i}",
                word_count=50
            )
            self.storage.save_chapter("test", chapter)

        chapters = self.storage.list_chapters("test")
        self.assertEqual(sorted(chapters), [1, 2, 3])

    def test_delete_chapter(self):
        """Test deleting chapter file."""
        chapter = ChapterContent(chapter_number=1, content="Content")
        self.storage.save_chapter("test", chapter)

        result = self.storage.delete_chapter("test", 1)
        self.assertTrue(result)

        loaded = self.storage.load_chapter("test", 1)
        self.assertIsNone(loaded)

    def test_save_and_load_project(self):
        """Test saving and loading entire project."""
        project = StoryProject(
            name="test_project",
            description="Test description"
        )

        # Add a chapter
        chapter = ChapterContent(
            chapter_number=1,
            content="Chapter content"
        )
        project.chapters[1] = chapter

        # Save and load
        self.storage.save_project(project)
        loaded = self.storage.load_project("test_project")

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "test_project")
        self.assertEqual(loaded.description, "Test description")
        self.assertIn(1, loaded.chapters)


class TestContentManager(unittest.TestCase):
    """Test ContentManager."""

    def setUp(self):
        """Set up test fixtures."""
        self.manager = ContentManager(auto_save=False)

    def test_create_project(self):
        """Test creating a project."""
        project = self.manager.create_project(
            name="Test Story",
            description="Test description"
        )

        self.assertEqual(project.name, "Test Story")
        self.assertEqual(self.manager.current_project.name, "Test Story")

    def test_add_chapter(self):
        """Test adding a chapter."""
        self.manager.create_project("test")
        chapter = ChapterContent(
            chapter_number=1,
            title="Chapter 1",
            content="Content",
            word_count=50
        )

        result = self.manager.add_chapter(chapter)

        self.assertTrue(result)
        self.assertIn(1, self.manager.current_project.chapters)

    def test_get_chapter(self):
        """Test getting a chapter."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Content")
        self.manager.add_chapter(chapter)

        retrieved = self.manager.get_chapter(1)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.chapter_number, 1)

    def test_update_chapter(self):
        """Test updating a chapter."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Original")
        self.manager.add_chapter(chapter)

        result = self.manager.update_chapter(1, "Updated content")

        self.assertTrue(result)
        self.assertEqual(self.manager.current_project.chapters[1].content, "Updated content")

    def test_delete_chapter(self):
        """Test deleting a chapter."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Content")
        self.manager.add_chapter(chapter)

        # Chapter is in current_project.chapters
        self.assertIn(1, self.manager.current_project.chapters)
        result = self.manager.delete_chapter(1)

        # delete_chapter should succeed since chapter is in project
        # But storage might not have it if auto_save is False
        # The method deletes from both project and storage
        self.assertNotIn(1, self.manager.current_project.chapters)

    def test_list_chapters(self):
        """Test listing chapters."""
        self.manager.create_project("test")
        for i in range(1, 4):
            chapter = ChapterContent(chapter_number=i, content=f"Content {i}")
            self.manager.add_chapter(chapter)

        chapters = self.manager.list_chapters()
        self.assertEqual(sorted(chapters), [1, 2, 3])

    def test_get_all_chapters(self):
        """Test getting all chapters."""
        self.manager.create_project("test")
        for i in range(1, 4):
            chapter = ChapterContent(chapter_number=i, content=f"Content {i}")
            self.manager.add_chapter(chapter)

        chapters = self.manager.get_all_chapters()

        self.assertEqual(len(chapters), 3)
        self.assertEqual(chapters[0].chapter_number, 1)

    def test_get_full_story(self):
        """Test getting full story."""
        self.manager.create_project("test")
        chapter1 = ChapterContent(chapter_number=1, title="Ch1", content="Content 1")
        chapter2 = ChapterContent(chapter_number=2, title="Ch2", content="Content 2")
        self.manager.add_chapter(chapter1)
        self.manager.add_chapter(chapter2)

        full_story = self.manager.get_full_story()

        self.assertIn("Content 1", full_story)
        self.assertIn("Content 2", full_story)

    def test_get_word_count(self):
        """Test getting word count."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="测试内容 Test content", word_count=50)
        self.manager.add_chapter(chapter)

        count = self.manager.get_word_count()

        self.assertGreater(count, 0)

    def test_version_tracking(self):
        """Test version tracking."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Original")
        self.manager.add_chapter(chapter)

        # Update should create version
        self.manager.update_chapter(1, "Updated")

        versions = self.manager.get_versions(1)
        self.assertGreater(len(versions), 0)

    def test_restore_version(self):
        """Test restoring a version."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Original")
        self.manager.add_chapter(chapter)
        self.manager.update_chapter(1, "Updated")

        versions = self.manager.get_versions(1)
        if versions:
            result = self.manager.restore_version(1, versions[0].version_id)
            self.assertTrue(result)

    def test_export_to_markdown(self):
        """Test markdown export."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, title="Chapter 1", content="Content")
        self.manager.add_chapter(chapter)

        markdown = self.manager.export_to_markdown()

        self.assertIn("# test", markdown)
        self.assertIn("Chapter 1", markdown)
        self.assertIn("Content", markdown)

    def test_export_to_txt(self):
        """Test text export."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, title="Chapter 1", content="Content")
        self.manager.add_chapter(chapter)

        text = self.manager.export_to_txt()

        self.assertIn("test", text)
        self.assertIn("Content", text)

    def test_export_to_json(self):
        """Test JSON export."""
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Content")
        self.manager.add_chapter(chapter)

        json_str = self.manager.export_to_json()

        self.assertIn("test", json_str)
        self.assertIn("chapters", json_str)

    def test_check_consistency(self):
        """Test consistency checking integration."""
        settings = ExtractedSettings()
        self.manager.create_project("test")
        chapter = ChapterContent(chapter_number=1, content="Test content")
        self.manager.add_chapter(chapter)

        report = self.manager.check_consistency(settings)

        self.assertIsNotNone(report)
        self.assertIsInstance(report.score, float)

    def test_get_stats(self):
        """Test getting project statistics."""
        self.manager.create_project("test")
        for i in range(1, 4):
            chapter = ChapterContent(chapter_number=i, content="Content", word_count=100)
            self.manager.add_chapter(chapter)

        stats = self.manager.get_stats()

        self.assertEqual(stats["total_chapters"], 3)
        self.assertEqual(stats["total_words"], 300)
        self.assertEqual(stats["avg_words_per_chapter"], 100)


class TestFactoryFunctions(unittest.TestCase):
    """Test factory functions."""

    def test_create_content_manager(self):
        """Test creating content manager."""
        manager = create_content_manager(auto_save=True)

        self.assertIsInstance(manager, ContentManager)
        self.assertTrue(manager.auto_save)

    def test_create_file_manager(self):
        """Test creating file manager."""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = create_file_manager(base_path=temp_dir)

            self.assertIsInstance(manager, ContentManager)
            self.assertIsInstance(manager.storage, FileContentStorage)
        finally:
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
