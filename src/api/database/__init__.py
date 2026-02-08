"""
数据库初始化模块

提供SQLite和PostgreSQL数据库引擎和会话管理
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool, QueuePool
import logging
import os

from .base import Base
from .config import get_database_url, get_settings, get_engine_kwargs
from .models import (
    SessionModel,
    MessageModel,
    Project,
    Chapter,
    ChapterVersion,
    GenerationTask,
)

logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()
database_url = get_database_url()
engine_kwargs = get_engine_kwargs()

# 根据数据库类型配置连接池
if settings.database_type == "postgresql":
    # PostgreSQL 使用 QueuePool（默认）
    engine = create_async_engine(
        database_url,
        **engine_kwargs,
        poolclass=QueuePool,
        pool_pre_ping=True,
    )
    logger.info("Using PostgreSQL with QueuePool")
else:
    # SQLite 使用 NullPool（因为SQLite不支持连接池）
    engine = create_async_engine(
        database_url,
        echo=settings.echo_sql,
        pool_pre_ping=True,
        poolclass=NullPool,
        connect_args={"check_same_thread": False},  # SQLite特定配置
    )
    logger.info("Using SQLite with NullPool")

# 创建异步会话工厂
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """初始化数据库，创建所有表"""
    try:
        from .config import get_database_path
        db_path = get_database_path()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("Database connection closed")


async def get_db() -> AsyncSession:
    """
    获取数据库会话的依赖注入函数

    用法:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


__all__ = [
    "engine",
    "AsyncSessionLocal",
    "init_db",
    "close_db",
    "get_db",
    "Base",
    # Models
    "SessionModel",
    "MessageModel",
    "Project",
    "Chapter",
    "ChapterVersion",
    "GenerationTask",
]
