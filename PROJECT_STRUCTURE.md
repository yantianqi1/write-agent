#!/bin/bash
# 项目文件结构
/root/小说agent
├── README.md
├── claude.md
├── requirements.txt
├── config.yaml
├── run_tests.sh
├── list_files.sh
│
├── src/
│   ├── __init__.py
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── base.py              # 记忆系统基础接口
│   │   ├── hierarchical.py      # 分层记忆系统实现
│   │   ├── mock_store.py         # Mock 记忆存储
│   │   ├── mock_vector_store.py # Mock 向量存储
│   │   └── chroma_store.py       # Chroma 向量存储
│   │
│   └── story/
│       ├── __init__.py
│       ├── material_collector.py         # 素材收集模块（已完成）
│       ├── local_knowledge_collector.py  # 本地知识库收集器（已完成）
│       └── web_search_collector.py          # 联网搜索收集器（已完成）
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_memory_base.py
│   ├── test_memory_hierarchical.py
│   ├── test_chroma_store.py
│   └── test_material_collector.py  # 素材收集模块测试（已完成）
│
├── examples/
│   ├── memory_usage.py
│   └── material_collector_usage.py  # 素材收集使用示例（已完成）
│
└── data/
    └── .gitkeep
