"""
数据库迁移脚本

用于初始化数据库和执行迁移
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.database import init_db, close_db


async def main():
    """主函数"""
    print("Initializing database...")
    try:
        await init_db()
        print("✓ Database initialized successfully")
        print(f"  Database location: ./data/writeagent.db")
    except Exception as e:
        print(f"✗ Failed to initialize database: {e}")
        sys.exit(1)
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
