"""
Content management module.

This module provides management of generated content including
storage, retrieval, version control, and export functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime
from pathlib import Path

from .content_generator import ChapterContent, GenerationResult
from .consistency import ConsistencyReport, ConsistencyChecker


class StorageBackend(Enum):
    """Type of storage backend."""
    MEMORY = "memory"
    FILE = "file"
    DATABASE = "database"


@dataclass
class ContentVersion:
    """A version of content."""
    version_id: str
    content: str
    created_at: str
    author: str = "AI"
    change_description: str = ""
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version_id": self.version_id,
            "content": self.content,
            "created_at": self.created_at,
            "author": self.author,
            "change_description": self.change_description,
            "word_count": self.word_count,
        }


@dataclass
class StoryProject:
    """A complete story project with all chapters and metadata."""
    name: str
    description: str = ""
    chapters: Dict[int, ChapterContent] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    modified_at: str = ""
    version: int = 1

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.modified_at:
            self.modified_at = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "chapters": {str(k): v.to_dict() for k, v in self.chapters.items()},
            "metadata": self.metadata.copy(),
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "version": self.version,
        }


class ContentStorage(ABC):
    """Abstract base class for content storage backends."""

    @abstractmethod
    def save_chapter(self, project_name: str, chapter: ChapterContent) -> bool:
        """Save a chapter."""
        pass

    @abstractmethod
    def load_chapter(self, project_name: str, chapter_number: int) -> Optional[ChapterContent]:
        """Load a chapter."""
        pass

    @abstractmethod
    def list_chapters(self, project_name: str) -> List[int]:
        """List all chapter numbers."""
        pass

    @abstractmethod
    def delete_chapter(self, project_name: str, chapter_number: int) -> bool:
        """Delete a chapter."""
        pass


class MemoryContentStorage(ContentStorage):
    """In-memory storage for content."""

    def __init__(self):
        """Initialize memory storage."""
        self.projects: Dict[str, Dict[int, ChapterContent]] = {}

    def save_chapter(self, project_name: str, chapter: ChapterContent) -> bool:
        """Save a chapter to memory."""
        if project_name not in self.projects:
            self.projects[project_name] = {}
        self.projects[project_name][chapter.chapter_number] = chapter
        return True

    def load_chapter(self, project_name: str, chapter_number: int) -> Optional[ChapterContent]:
        """Load a chapter from memory."""
        return self.projects.get(project_name, {}).get(chapter_number)

    def list_chapters(self, project_name: str) -> List[int]:
        """List all chapter numbers."""
        if project_name not in self.projects:
            return []
        return list(self.projects[project_name].keys())

    def delete_chapter(self, project_name: str, chapter_number: int) -> bool:
        """Delete a chapter from memory."""
        if project_name in self.projects and chapter_number in self.projects[project_name]:
            del self.projects[project_name][chapter_number]
            return True
        return False


class FileContentStorage(ContentStorage):
    """File-based storage for content."""

    def __init__(self, base_path: str = "./data/stories"):
        """Initialize file storage."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_project_path(self, project_name: str) -> Path:
        """Get the directory path for a project."""
        project_path = self.base_path / project_name
        project_path.mkdir(parents=True, exist_ok=True)
        return project_path

    def _get_chapter_path(self, project_name: str, chapter_number: int) -> Path:
        """Get the file path for a chapter."""
        return self._get_project_path(project_name) / f"chapter_{chapter_number:03d}.json"

    def save_chapter(self, project_name: str, chapter: ChapterContent) -> bool:
        """Save a chapter to file."""
        path = self._get_chapter_path(project_name, chapter.chapter_number)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(chapter.to_dict(), f, ensure_ascii=False, indent=2)
        return True

    def load_chapter(self, project_name: str, chapter_number: int) -> Optional[ChapterContent]:
        """Load a chapter from file."""
        path = self._get_chapter_path(project_name, chapter_number)
        if not path.exists():
            return None

        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return ChapterContent(
            chapter_number=data["chapter_number"],
            title=data.get("title", ""),
            content=data.get("content", ""),
            word_count=data.get("word_count", 0),
            summary=data.get("summary", ""),
            outline=data.get("outline", ""),
            characters=data.get("characters", []),
            locations=data.get("locations", []),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
        )

    def list_chapters(self, project_name: str) -> List[int]:
        """List all chapter numbers."""
        project_path = self._get_project_path(project_name)
        if not project_path.exists():
            return []

        chapters = []
        for path in project_path.glob("chapter_*.json"):
            # Extract chapter number from filename
            try:
                num = int(path.stem.split("_")[1])
                chapters.append(num)
            except (ValueError, IndexError):
                continue

        return sorted(chapters)

    def delete_chapter(self, project_name: str, chapter_number: int) -> bool:
        """Delete a chapter file."""
        path = self._get_chapter_path(project_name, chapter_number)
        if path.exists():
            path.unlink()
            return True
        return False

    def save_project(self, project: StoryProject) -> bool:
        """Save entire project to file."""
        project_path = self._get_project_path(project.name)
        meta_path = project_path / "project.json"

        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(project.to_dict(), f, ensure_ascii=False, indent=2)

        # Save all chapters
        for chapter in project.chapters.values():
            self.save_chapter(project.name, chapter)

        return True

    def load_project(self, project_name: str) -> Optional[StoryProject]:
        """Load entire project from file."""
        project_path = self._get_project_path(project_name)
        meta_path = project_path / "project.json"

        if not meta_path.exists():
            return None

        with open(meta_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Load chapters
        chapters = {}
        for num in self.list_chapters(project_name):
            chapter = self.load_chapter(project_name, num)
            if chapter:
                chapters[num] = chapter

        return StoryProject(
            name=data["name"],
            description=data.get("description", ""),
            chapters=chapters,
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", ""),
            modified_at=data.get("modified_at", ""),
            version=data.get("version", 1),
        )


class ContentManager:
    """
    Main content manager for story projects.

    Provides:
    - Chapter CRUD operations
    - Version control
    - Export functionality
    - Consistency checking integration
    """

    def __init__(self,
                 storage: Optional[ContentStorage] = None,
                 auto_save: bool = True):
        """
        Initialize the content manager.

        Args:
            storage: Storage backend (defaults to MemoryContentStorage)
            auto_save: Whether to auto-save after each modification
        """
        self.storage = storage or MemoryContentStorage()
        self.auto_save = auto_save
        self.current_project: Optional[StoryProject] = None
        self.chapter_versions: Dict[str, List[ContentVersion]] = {}

    def create_project(self, name: str, description: str = "") -> StoryProject:
        """Create a new project."""
        self.current_project = StoryProject(
            name=name,
            description=description
        )
        return self.current_project

    def load_project(self, name: str) -> Optional[StoryProject]:
        """Load a project from storage."""
        if isinstance(self.storage, FileContentStorage):
            self.current_project = self.storage.load_project(name)
        else:
            # For memory storage, create empty project
            self.current_project = StoryProject(name=name)
        return self.current_project

    def save_project(self) -> bool:
        """Save current project."""
        if not self.current_project:
            return False

        self.current_project.modified_at = datetime.now().isoformat()

        if isinstance(self.storage, FileContentStorage):
            return self.storage.save_project(self.current_project)

        # For memory storage, save all chapters
        for chapter in self.current_project.chapters.values():
            self.storage.save_chapter(self.current_project.name, chapter)

        return True

    def add_chapter(self, chapter: ChapterContent) -> bool:
        """Add a chapter to the current project."""
        if not self.current_project:
            return False

        # Save version before modification
        if chapter.chapter_number in self.current_project.chapters:
            self._save_version(chapter.chapter_number,
                             self.current_project.chapters[chapter.chapter_number])

        self.current_project.chapters[chapter.chapter_number] = chapter

        if self.auto_save:
            self.storage.save_chapter(self.current_project.name, chapter)

        return True

    def get_chapter(self, chapter_number: int) -> Optional[ChapterContent]:
        """Get a chapter from the current project."""
        if not self.current_project:
            return None

        if chapter_number in self.current_project.chapters:
            return self.current_project.chapters[chapter_number]

        # Try loading from storage
        if self.current_project:
            chapter = self.storage.load_chapter(
                self.current_project.name, chapter_number
            )
            if chapter:
                self.current_project.chapters[chapter_number] = chapter
                return chapter

        return None

    def update_chapter(self,
                      chapter_number: int,
                      new_content: str,
                      change_description: str = "") -> bool:
        """Update a chapter's content."""
        chapter = self.get_chapter(chapter_number)
        if not chapter:
            return False

        # Save version
        self._save_version(chapter_number, chapter)

        # Update
        chapter.content = new_content
        chapter.word_count = self._count_words(new_content)
        chapter.modified_at = datetime.now().isoformat()

        if self.auto_save:
            self.storage.save_chapter(self.current_project.name, chapter)

        return True

    def delete_chapter(self, chapter_number: int) -> bool:
        """Delete a chapter."""
        if not self.current_project:
            return False

        if chapter_number in self.current_project.chapters:
            del self.current_project.chapters[chapter_number]

        return self.storage.delete_chapter(self.current_project.name, chapter_number)

    def list_chapters(self) -> List[int]:
        """List all chapter numbers."""
        if not self.current_project:
            return []

        numbers = list(self.current_project.chapters.keys())

        # Also check storage
        storage_numbers = self.storage.list_chapters(self.current_project.name)

        return sorted(set(numbers + storage_numbers))

    def get_all_chapters(self) -> List[ChapterContent]:
        """Get all chapters in order."""
        numbers = self.list_chapters()
        chapters = []

        for num in numbers:
            chapter = self.get_chapter(num)
            if chapter:
                chapters.append(chapter)

        return chapters

    def get_full_story(self) -> str:
        """Get the full story as a single string."""
        chapters = self.get_all_chapters()
        return "\n\n".join(
            f"{chapter.title}\n\n{chapter.content}"
            for chapter in chapters
        )

    def get_word_count(self) -> int:
        """Get total word count of all chapters."""
        return sum(ch.word_count for ch in self.get_all_chapters())

    def _save_version(self, chapter_number: int, chapter: ChapterContent) -> None:
        """Save a version of a chapter."""
        version_key = f"{self.current_project.name}_{chapter_number}"

        version = ContentVersion(
            version_id=f"v{datetime.now().timestamp()}",
            content=chapter.content,
            created_at=datetime.now().isoformat(),
            word_count=chapter.word_count
        )

        if version_key not in self.chapter_versions:
            self.chapter_versions[version_key] = []

        self.chapter_versions[version_key].append(version)

        # Keep only last 10 versions
        if len(self.chapter_versions[version_key]) > 10:
            self.chapter_versions[version_key] = self.chapter_versions[version_key][-10:]

    def get_versions(self, chapter_number: int) -> List[ContentVersion]:
        """Get all versions of a chapter."""
        version_key = f"{self.current_project.name}_{chapter_number}"
        return self.chapter_versions.get(version_key, [])

    def restore_version(self, chapter_number: int, version_id: str) -> bool:
        """Restore a chapter to a previous version."""
        versions = self.get_versions(chapter_number)
        target = next((v for v in versions if v.version_id == version_id), None)

        if not target:
            return False

        return self.update_chapter(
            chapter_number,
            target.content,
            f"Restored to {version_id}"
        )

    def export_to_markdown(self, output_path: str = None) -> str:
        """Export the story to markdown format."""
        if not output_path and self.current_project:
            output_path = f"./{self.current_project.name}.md"

        chapters = self.get_all_chapters()
        markdown = f"# {self.current_project.name if self.current_project else 'Story'}\n\n"

        if self.current_project and self.current_project.description:
            markdown += f"{self.current_project.description}\n\n---\n\n"

        for chapter in chapters:
            markdown += f"## {chapter.title}\n\n"
            markdown += f"{chapter.content}\n\n"

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(markdown)

        return markdown

    def export_to_txt(self, output_path: str = None) -> str:
        """Export the story to plain text format."""
        if not output_path and self.current_project:
            output_path = f"./{self.current_project.name}.txt"

        chapters = self.get_all_chapters()
        text = f"{self.current_project.name if self.current_project else 'Story'}\n\n"

        for chapter in chapters:
            text += f"{chapter.title}\n\n"
            text += f"{chapter.content}\n\n"

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)

        return text

    def export_to_json(self, output_path: str = None) -> str:
        """Export the story to JSON format."""
        if not output_path and self.current_project:
            output_path = f"./{self.current_project.name}.json"

        if self.current_project:
            json_data = self.current_project.to_dict()
        else:
            json_data = {"chapters": {}}

        json_str = json.dumps(json_data, ensure_ascii=False, indent=2)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def check_consistency(self,
                         settings,
                         checker: ConsistencyChecker = None) -> ConsistencyReport:
        """Check consistency of all chapters."""
        if not checker:
            from .consistency import create_consistency_checker
            checker = create_consistency_checker(settings)

        chapters = self.get_all_chapters()
        chapters_data = [(ch.chapter_number, ch.content) for ch in chapters]

        return checker.check_full_story(chapters_data)

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the story."""
        chapters = self.get_all_chapters()

        return {
            "total_chapters": len(chapters),
            "total_words": self.get_word_count(),
            "avg_words_per_chapter": self.get_word_count() // len(chapters) if chapters else 0,
            "chapter_numbers": [ch.chapter_number for ch in chapters],
            "has_outline": any(ch.outline for ch in chapters),
        }

    def _count_words(self, text: str) -> int:
        """Count words in mixed Chinese-English text."""
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len(text.split()) - chinese_chars
        return chinese_chars + english_words


def create_content_manager(storage: Optional[ContentStorage] = None,
                          auto_save: bool = True) -> ContentManager:
    """
    Factory function to create content managers.

    Args:
        storage: Optional storage backend
        auto_save: Whether to auto-save modifications

    Returns:
        Configured ContentManager
    """
    return ContentManager(storage, auto_save)


def create_file_manager(base_path: str = "./data/stories") -> ContentManager:
    """Create a content manager with file storage."""
    storage = FileContentStorage(base_path)
    return ContentManager(storage, auto_save=True)
