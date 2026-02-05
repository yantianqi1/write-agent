#!/bin/bash
# 运行素材收集模块测试

cd /root/小说agent

echo "========================================="
echo "运行素材收集模块测试"
echo "========================================="
echo ""

# 检查 Python 环境
python3 --version

# 安装依赖（如果需要）
pip3 install pytest -q

# 运行测试
python3 -m pytest tests/test_material_collector.py -v --tb=short

echo ""
echo "========================================="
echo "测试完成"
echo "========================================="
