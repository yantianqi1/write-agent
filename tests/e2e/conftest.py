"""
E2E test fixtures and configuration

This module provides fixtures for end-to-end testing with isolated test databases.
"""

import pytest
import asyncio
from typing import AsyncGenerator
from pathlib import Path
import tempfile
import shutil

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Import models and database functions
from api.database import Base
from api.database.models import Project, Session, Message


@pytest.fixture(scope="module")
async def e2e_test_engine():
    """
    Create an isolated test database for E2E tests.

    Uses a file-based SQLite database for better compatibility with
    concurrent tests and to test persistence behavior.
    """
    # Create a temporary database file
    db_file = Path(tempfile.mktemp(suffix=".db"))

    engine = create_async_engine(
        f"sqlite+aiosqlite:///{db_file}",
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()
    if db_file.exists():
        db_file.unlink()


@pytest.fixture(scope="module")
async def e2e_test_session_maker(e2e_test_engine):
    """
    Create a session maker for E2E tests.
    """
    return async_sessionmaker(
        e2e_test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )


@pytest.fixture
async def e2e_test_session(e2e_test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh session for each E2E test.

    Each test gets a clean database state.
    """
    async with e2e_test_session_maker() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def clean_db(e2e_test_engine):
    """
    Clean all data from the test database between tests.

    Useful for tests that need a fresh start but share the engine.
    """
    async with e2e_test_engine.begin() as conn:
        # Delete all data but keep schema
        await conn.run_sync(lambda sync_conn: [
            sync_conn.execute(table.delete()) for table in reversed(Base.metadata.sorted_tables)
        ])


@pytest.fixture
def test_project_data():
    """
    Provide test project data for E2E tests.
    """
    return {
        "name": "Test Project",
        "description": "A test project for E2E testing",
        "genre": "Fantasy",
        "target_word_count": 50000,
    }


@pytest.fixture
def test_session_data():
    """
    Provide test session data for E2E tests.
    """
    return {
        "session_id": "test-session-123",
        "title": "Test Chat Session",
    }


@pytest.fixture
def test_message_data():
    """
    Provide test message data for E2E tests.
    """
    return [
        {
            "role": "user",
            "content": "Hello, this is a test message."
        },
        {
            "role": "assistant",
            "content": "Hello! I'm the AI writing assistant. How can I help you today?"
        },
    ]
