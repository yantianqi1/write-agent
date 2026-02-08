#!/usr/bin/env python3
"""
数据库迁移执行脚本

运行Alembic迁移来更新数据库schema
"""

import subprocess
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_command(cmd: list[str], description: str) -> bool:
    """运行命令"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}", file=sys.stderr)
        return False

    return True


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Database migration tool")
    parser.add_argument(
        "action",
        choices=["upgrade", "downgrade", "current", "history", "revision"],
        help="Migration action",
        default="upgrade",
        nargs="?"
    )
    parser.add_argument(
        "--revision",
        "-r",
        help="Revision ID (for downgrade/upgrade to specific version)",
        default=None
    )
    parser.add_argument(
        "--message",
        "-m",
        help="Migration message (for revision)",
        default=None
    )
    parser.add_argument(
        "--autogenerate",
        "-a",
        help="Auto-generate migration from models",
        action="store_true"
    )

    args = parser.parse_args()

    # Alembic可执行文件路径
    alembic_cmd = [sys.executable, "-m", "alembic"]

    if args.action == "upgrade":
        revision = args.revision or "head"
        cmd = alembic_cmd + ["upgrade", revision]
        run_command(cmd, f"Upgrading database to {revision}")

    elif args.action == "downgrade":
        if not args.revision:
            print("Error: --revision is required for downgrade", file=sys.stderr)
            sys.exit(1)
        cmd = alembic_cmd + ["downgrade", args.revision]
        run_command(cmd, f"Downgrading database to {args.revision}")

    elif args.action == "current":
        cmd = alembic_cmd + ["current"]
        run_command(cmd, "Showing current revision")

    elif args.action == "history":
        cmd = alembic_cmd + ["history"]
        run_command(cmd, "Showing migration history")

    elif args.action == "revision":
        cmd = ["revision"]
        if args.autogenerate:
            cmd.append("--autogenerate")
        if args.message:
            cmd.extend(["-m", args.message])
        cmd = alembic_cmd + cmd
        run_command(cmd, "Creating new migration")


if __name__ == "__main__":
    main()
