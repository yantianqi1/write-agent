#!/bin/bash
# 安装小说创作 Agent 依赖

set -e

echo "========================================="
echo "小说智能创作 Agent - 依赖安装"
echo "========================================="
echo ""

# 检查 Python 版本
echo "检查 Python 版本..."
python3 --version

# 检查 pip
echo ""
echo "检查 pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 未安装，请先安装 pip3"
    echo "   Ubuntu/Debian: sudo apt install python3-pip"
    echo "   CentOS/RHEL: sudo yum install python3-pip"
    exit 1
fi

# 安装依赖
echo ""
echo "安装 Python 依赖..."
pip3 install -r requirements.txt

# 创建数据目录
echo ""
echo "创建数据目录..."
mkdir -p data/memory
mkdir -p data/vector_db
mkdir -p data/stories

# 运行测试
echo ""
echo "运行测试..."
PYTHONPATH=$(pwd)/src python3 tests/simple_test.py

echo ""
echo "========================================="
echo "✅ 安装完成！"
echo "========================================="
echo ""
echo "使用示例："
echo "  python3 examples/memory_example.py"
echo ""
