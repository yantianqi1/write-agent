#!/usr/bin/env python3
"""
数据库初始化脚本

创建数据库文件和所有表
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def main():
    """主函数"""
    from src.api.database import init_db, get_database_url
    from src.api.database.config import get_database_path
    import logging

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    print("Initializing database...")
    print(f"Database URL: {get_database_url()}")
    print(f"Database path: {get_database_path()}")

    try:
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
