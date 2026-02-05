# 快速开始指南

## 环境要求

- Python 3.10+
- pip

## 安装

1. 克隆项目（如果还没有）
```bash
cd /path/to/project
```

2. 运行安装脚本
```bash
./install.sh
```

或者手动安装依赖：
```bash
pip3 install -r requirements.txt
```

## 运行示例

### 1. 记忆系统示例

```bash
python3 examples/memory_example.py
```

这个示例展示了：
- 基础记忆操作（添加、获取、更新、删除）
- 记忆搜索功能
- 按层级获取记忆
- 向量存储集成
- RAG 工作流

### 2. 运行测试

```bash
PYTHONPATH=$(pwd)/src python3 tests/simple_test.py
```

## 项目结构

```
小说agent/
├── src/                    # 源代码
│   ├── memory/             # 记忆系统
│   ├── story/              # 创作流程（开发中）
│   ├── utils/              # 工具函数（开发中）
│   └── api/                # API 服务（开发中）
├── tests/                  # 测试
├── examples/               # 示例代码
├── config/                 # 配置文件
├── data/                   # 数据存储
├── requirements.txt        # 依赖列表
└── README.md              # 项目说明
```

## 核心功能

### 记忆系统

记忆系统是小说创作的核心，用于存储和管理创作过程中的各种信息。

#### 五层记忆架构

1. **全局记忆 (GLOBAL)**：世界观设定、核心主题、整体大纲
2. **角色记忆 (CHARACTER)**：人物档案、性格特征、关系图谱
3. **情节记忆 (PLOT)**：已发生事件、伏笔列表、未解决冲突
4. **近期上下文 (CONTEXT)**：最近2-3章的详细内容
5. **风格记忆 (STYLE)**：叙事风格、常用表达、节奏模式

#### 使用示例

```python
from memory.base import MemoryLevel, MemoryItem
from memory.hierarchical import HierarchicalMemory
from memory.vector import MockVectorStore

# 创建记忆系统
memory = HierarchicalMemory(storage_path="./data/memory")

# 添加全局记忆
memory.add(MemoryItem(
    level=MemoryLevel.GLOBAL,
    content="世界背景：这是一个魔法世界",
    metadata={"type": "world_setting"}
))

# 添加角色记忆
memory.add(MemoryItem(
    level=MemoryLevel.CHARACTER,
    content="主角林风：18岁，天生元素亲和力",
    metadata={"name": "林风", "age": 18}
))

# 搜索记忆
results = memory.search("林风", limit=5)
for item in results:
    print(f"[{item.level.value}] {item.content}")
```

## 开发进度

详细进度请查看 [claude.md](./claude.md)

### 当前状态

- ✅ 阶段 1：基础架构搭建
- ⏳ 阶段 2：记忆系统实现
- 🔜 阶段 3：核心功能开发

## 下一步

- 实现素材收集模块
- 开发大纲生成功能
- 实现章节细化算法
- 构建正文生成引擎

## 贡献

欢迎贡献代码、报告问题或提出建议！

## 许可证

MIT License
