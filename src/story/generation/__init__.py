"""
Content generation module.

Integrates LLM providers with prompt templates to generate
high-quality story content while maintaining consistency.
"""

from .prompt_templates import (
    GenerationMode,
    ContentType,
    GenerationContext,
    PromptTemplate,
    TemplateEngine,
    StoryTemplateEngine,
    CompactTemplateEngine,
    create_template_engine
)

from .content_generator import (
    GenerationRequest,
    GenerationResult,
    ContentGenerator,
    LLMContentGenerator,
    ChapterContent,
    StoryGenerator,
    create_content_generator,
    create_story_generator
)

from .consistency import (
    ConsistencyLevel,
    ConsistencyIssue,
    ConsistencyReport,
    CharacterTracker,
    WorldRuleChecker,
    PlotConsistencyChecker,
    ConsistencyChecker,
    create_consistency_checker
)

from .content_manager import (
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

__all__ = [
    # Prompt templates
    "GenerationMode",
    "ContentType",
    "GenerationContext",
    "PromptTemplate",
    "TemplateEngine",
    "StoryTemplateEngine",
    "CompactTemplateEngine",
    "create_template_engine",

    # Content generation
    "GenerationRequest",
    "GenerationResult",
    "ContentGenerator",
    "LLMContentGenerator",
    "ChapterContent",
    "StoryGenerator",
    "create_content_generator",
    "create_story_generator",

    # Consistency
    "ConsistencyLevel",
    "ConsistencyIssue",
    "ConsistencyReport",
    "CharacterTracker",
    "WorldRuleChecker",
    "PlotConsistencyChecker",
    "ConsistencyChecker",
    "create_consistency_checker",

    # Content management
    "StorageBackend",
    "ContentVersion",
    "StoryProject",
    "ContentStorage",
    "MemoryContentStorage",
    "FileContentStorage",
    "ContentManager",
    "create_content_manager",
    "create_file_manager",
]

__version__ = "0.1.0"
