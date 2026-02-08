"""
pytest configuration and shared fixtures

This module provides shared fixtures for all tests.
"""

import sys
from pathlib import Path

# Add src to Python path for all tests
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
import asyncio
from typing import AsyncGenerator, Generator
import tempfile
import shutil

from api.database import Base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an instance of the default event loop for the test session.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """
    Create a test database engine.

    Uses an in-memory SQLite database for fast, isolated tests.
    """
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        echo=False,
        future=True
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    The session is rolled back after each test to ensure isolation.
    """
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        # Roll back to clean up after test
        await session.rollback()


@pytest.fixture
def temp_storage_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for file storage tests.

    The directory is cleaned up after the test.
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    # Clean up
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
