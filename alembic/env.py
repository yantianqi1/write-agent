"""
Alembic环境配置

用于数据库迁移
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 导入配置和模型
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.database import Base
from src.api.database.models import (
    SessionModel,
    MessageModel,
    Project,
    Chapter,
    ChapterVersion,
    GenerationTask,
)

# Alembic配置对象
config = context.config

# 解释配置文件的Python日志记录
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象
target_metadata = Base.metadata

# 其他从Alembic上下文中获取的值
# my_important_option = config.get_main_option("my_important_option")


def get_url():
    """从配置获取数据库URL"""
    from src.api.database.config import get_database_url
    return get_database_url()


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移。

    这将配置上下文，只需一个URL即可，而不是一个Engine，
    尽管在这里也接受Engine。通过跳过Engine创建，我们甚至不需要DBAPI可用。

    对此上下文的调用`context.execute()`时，将给定的字符串输出到脚本输出。
    """
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """运行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """运行异步迁移"""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移。

    这种情况下，我们需要创建一个Engine并将连接与该上下文关联。
    """
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
