"""
数据库配置

从环境变量读取数据库配置，支持 SQLite 和 PostgreSQL
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    # 数据库类型
    database_type: str = "sqlite"  # 'sqlite' or 'postgresql'

    # SQLite 配置
    database_path: str = "./data/writeagent.db"

    # PostgreSQL 配置
    postgres_url: Optional[str] = None

    # SQLite 连接池配置（较小的值适合SQLite）
    sqlite_pool_size: int = 1
    sqlite_max_overflow: int = 0
    sqlite_pool_timeout: int = 30
    sqlite_pool_recycle: int = 3600

    # PostgreSQL 连接池配置（可以支持更多连接）
    postgres_pool_size: int = 20  # 增加到20
    postgres_max_overflow: int = 40  # 增加到40
    postgres_pool_timeout: int = 30
    postgres_pool_recycle: int = 3600  # 增加到1小时

    # 兼容旧配置（SQLite 优先）
    pool_size: int = 1
    max_overflow: int = 0
    pool_timeout: int = 30
    pool_recycle: int = 3600

    # 调试模式
    echo_sql: bool = False

    model_config = {
        "env_prefix": "DB_",
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"  # 忽略额外字段
    }

    def get_pool_settings(self) -> dict:
        """根据数据库类型返回相应的连接池配置"""
        if self.database_type == "postgresql":
            return {
                "pool_size": self.postgres_pool_size,
                "max_overflow": self.postgres_max_overflow,
                "pool_timeout": self.postgres_pool_timeout,
                "pool_recycle": self.postgres_pool_recycle,
            }
        else:  # SQLite
            return {
                "pool_size": self.sqlite_pool_size,
                "max_overflow": self.sqlite_max_overflow,
                "pool_timeout": self.sqlite_pool_timeout,
                "pool_recycle": self.sqlite_pool_recycle,
            }


@lru_cache()
def get_settings() -> DatabaseSettings:
    """获取数据库配置（单例）"""
    return DatabaseSettings()


def get_database_path() -> Path:
    """获取数据库文件路径（仅SQLite）"""
    settings = get_settings()
    path = Path(settings.database_path)

    # 确保数据目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def get_database_url() -> str:
    """
    获取数据库连接URL

    优先使用 DATABASE_URL 环境变量（完整连接字符串）
    否则根据 database_type 构建 URL
    """
    # 1. 优先检查完整的 DATABASE_URL
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    settings = get_settings()

    # 2. 检查 PostgreSQL 专用配置
    if settings.database_type == "postgresql":
        if settings.postgres_url:
            return settings.postgres_url
        # 从环境变量构建 PostgreSQL URL
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_user = os.getenv("POSTGRES_USER", "writeagent")
        pg_password = os.getenv("POSTGRES_PASSWORD", "")
        pg_db = os.getenv("POSTGRES_DB", "writeagent")
        return f"postgresql+asyncpg://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_db}"

    # 3. 默认使用 SQLite
    path = get_database_path()
    return f"sqlite+aiosqlite:///{path}"


def get_engine_kwargs() -> dict:
    """
    获取数据库引擎参数

    根据数据库类型返回不同的配置
    """
    settings = get_settings()

    if settings.database_type == "postgresql":
        return {
            "echo": settings.echo_sql,
            "pool_pre_ping": True,  # 连接前检查有效性
            **settings.get_pool_settings(),
        }
    else:  # SQLite
        return {
            "echo": settings.echo_sql,
            "pool_pre_ping": True,
            **settings.get_pool_settings(),
        }


__all__ = [
    "DatabaseSettings",
    "get_settings",
    "get_database_path",
    "get_database_url",
    "get_engine_kwargs",
]
