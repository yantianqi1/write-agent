# 小说智能创作 Agent

> 一个能够自动创作长篇小说的智能 Agent 系统。用户只需输入一句话或一段设定，系统即可自动完成从素材收集到全文生成的完整创作流程。

---

## 🎯 项目愿景

实现人机协作的高质量长篇小说创作，降低创作门槛的同时保证内容一致性和文学质量。

### 核心特性

- ✨ **一句话灵感输入** - 快速启动创作
- 🔍 **自动素材收集** - 检索数据库 + 联网搜索
- 🧠 **分层记忆系统** - 保证长篇一致性
- 🤝 **人机协作创作** - 用户审核 + 机器生成
- 🎨 **质量控制机制** - 多轮迭代优化

---

## 📁 项目结构

```
小说agent/
├── src/                          # 源代码目录
│   ├── memory/                    # 记忆系统模块 ✅ (100%)
│   │   ├── base.py               # 基础接口
│   │   ├── hierarchical.py       # 分层记忆系统
│   │   ├── mock_store.py          # Mock 存储
│   │   ├── mock_vector_store.py  # Mock 向量存储
│   │   └── chroma_store.py        # Chroma 向量存储
│   └── story/                      # 故事创作模块
│       ├── material_collector.py         # 素材收集模块 ✅ (100%)
│       ├── local_knowledge_collector.py  # 本地知识库收集器
│       └── web_search_collector.py          # 联网搜索收集器
│
├── tests/                        # 测试目录
│   ├── test_memory_base.py       # 记忆系统测试
│   ├── test_memory_hierarchical.py # 分层记忆测试
│   ├── test_chroma_store.py       # Chroma 测试
│   └── test_material_collector.py  # 素材收集测试
│
├── examples/                      # 使用示例
│   ├── memory_usage.py            # 记忆系统示例
│   └── material_collector_usage.py # 素材收集示例
│
├── data/                         # 数据存储
│
├── README.md                     # 项目说明 (本文件)
├── claude.md                      # 开发进度跟踪
├── PROJECT_STRUCTURE.md          # 项目结构说明
├── FILE_LIST.md                  # 文件清单
├── STATUS_REPORT.md              # 项目状态报告
├── requirements.txt              # Python 依赖
└── config.yaml                    # 应用配置
```

---

## 📊 开发进度

### 整体完成度：40%

```
记忆系统     ████████████████████████ 100% ████████████████████████
素材收集     ████████████████████████ 100% ████████████████████████
大纲生成       ░░░░░░░░░░░░░░░░░░░░░░░░░   0% ░░░░░░░░░░░░░░░░░░░░░░░░░
篇章细化       ░░░░░░░░░░░░░░░░░░░░░░░░░   0% ░░░░░░░░░░░░░░░░░░░░░░░░░
正文生成       ░░░░░░░░░░░░░░░░░░░░░░░░░   0% ░░░░░░░░░░░░░░░░░░░░░░░░░
用户审核       ░░░░░░░░░░░░░░░░░░░░░░░░░   0% ░░░░░░░░░░░░░░░░░░░░░░░░░
```

### 已完成模块 ✅

#### 1. 记忆系统模块 (100%)
- **基础接口** - `MemoryStore`, `MemoryLevel`, `MemoryItem`
- **分层记忆** - `HierarchicalMemory` 支持 5 种记忆层级
- **向量存储** - `VectorStore` 抽象接口
- **存储实现** - `MockVectorStore`, `ChromaVectorStore`
- **向量检索** - 语义相似度搜索和 RAG 集成

#### 2. 素材收集模块 (100%)
- **核心接口** - `Material`, `MaterialSource`, `MaterialCategory`
- **收集器实现**
  - `LocalKnowledgeCollector` - 从记忆系统检索素材
  - `WebSearchCollector` - 网络搜索收集
  - `CompositeMaterialCollector` - 多来源整合
- **智能处理**
  - `MaterialDeduplicator` - 内容哈希去重
  - `CredibilityEvaluator` - 多因素可信度评估
- **测试覆盖** - 100% 功能覆盖，80+ 测试用例
- **使用示例** - 7 个完整示例，详细注释

### 待开发模块 ⏳

#### 3. 大纲生成模块
- 基于用户输入生成大纲
- 使用记忆系统保持一致性
- 多轮迭代优化

#### 4. 篇章细化模块
- 章节结构设计
- 情节节点展开
- 伏笔埋设

#### 5. 正文生成引擎
- 章节内容生成
- 记忆上下文注入
- 风格一致性控制

#### 6. 用户审核接口
- 章节审核界面
- 修改建议收集
- 迭代优化机制

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd 小说agent

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行测试

```bash
# 运行所有测试
bash run_tests.sh

# 或使用 pytest
pytest tests/ -v
```

### 3. 运行示例

```bash
# 记忆系统示例
python examples/memory_usage.py

# 素材收集示例
python examples/material_collector_usage.py
```

### 4. 查看进度

```bash
# 开发进度跟踪
cat claude.md

# 项目状态报告
cat STATUS_REPORT.md

# 快速项目概览
cat QUICK_OVERVIEW.md
```

---

## 🏗️ 技术架构

### 技术栈

- **语言**：Python 3.8+
- **测试框架**：pytest
- **向量数据库**：Chroma (支持其他)
- **LLM 集成**：可集成 OpenAI Claude
- **配置管理**：PyYAML

### 核心模块

#### 记忆系统
```
MemoryLevel (记忆层级)
├── GLOBAL      - 全局设定、世界观
├── CHARACTER    - 角色设定、性格档案
├── PLOT         - 情节、事件、时间线
├── CONTEXT      - 近期上下文、对话
└── STYLE        - 风格、写作手法
```

#### 素材收集
```
MaterialSource (素材来源)
├── LOCAL_KNOWLEDGE - 本地知识库
├── WEB_SEARCH        - 联网搜索
├── USER_INPUT        - 用户输入
└── PREVIOUS_WORK     - 历史作品

MaterialCategory (素材分类)
├── CHARACTER   - 人物设定
├── SETTING     - 场景/世界观设定
├── PLOT         - 情节/事件
├── DIALOGUE     - 对话素材
├── DESCRIPTION - 描写素材
├── KNOWLEDGE    - 背景知识
└── REFERENCE    - 参考作品
```

---

## 📖 文档导航

### 项目文档
- **[README.md](./README.md)** - 项目说明和快速开始 (本文件)
- **[claude.md](./claude.md)** - 开发进度跟踪和任务清单
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 项目结构详细说明
- **[FILE_LIST.md](./FILE_LIST.md)** - 完整文件清单和代码统计
- **[STATUS_REPORT.md](./STATUS_REPORT.md)** - 项目状态报告和完成度分析
- **[QUICK_OVERVIEW.md](./QUICK_OVERVIEW.md)** - 快速项目概览

### 示例代码
- **[examples/memory_usage.py](./examples/memory_usage.py)** - 记忆系统使用示例
- **[examples/material_collector_usage.py](./examples/material_collector_usage.py)** - 素材收集使用示例

### 配置文件
- **[requirements.txt](./requirements.txt)** - Python 依赖列表
- **[config.yaml](./config.yaml)** - 应用配置文件

---

## 🧪 测试覆盖

### 测试统计
- **测试文件**：5 个
- **测试用例**：80+ 个
- **代码覆盖**：核心功能 100%
- **集成测试**：已覆盖

### 运行测试
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_material_collector.py -v

# 运行测试并生成覆盖率报告
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 代码统计

| 模块 | 代码行数 | 测试行数 | 示例行数 | 小计 |
|------|---------|---------|---------|------|
| 记忆系统 | ~1,355 | ~1,030 | ~542 | ~2,927 |
| 素材收集 | ~751 | ~402 | ~312 | ~1,465 |
| **总计** | **~2,106** | **~1,432** | **~854** | **~4,392** |

---

## 🎨 使用示例

### 素材收集

```python
from src.story.material_collector import CollectionRequest, MaterialCategory
from src.story.local_knowledge_collector import LocalKnowledgeCollector
from src.story.web_search_collector import MockWebSearchCollector
from src.story.material_collector import CompositeMaterialCollector

# 创建收集器
local_collector = LocalKnowledgeCollector(memory_store)
web_collector = MockWebSearchCollector()
composite = CompositeMaterialCollector([local_collector, web_collector])

# 创建请求
request = CollectionRequest(
    query="武侠剑法",
    category=MaterialCategory.KNOWLEDGE,
    max_results=10,
    use_local=True,
    use_web=True,
)

# 收集素材
result = composite.collect(request)

# 显示结果
for material in result.materials:
    print(f"- [{material.category.value}] {material.content}")
    print(f"  可信度: {material.credibility_score:.2f}")
```

更多示例请参见 [examples/](./examples/) 目录。

---

## 🔄 更新日志

### 2026-02-05 (今日)
- ✅ 完成素材收集模块开发
  - 实现核心接口和数据结构
  - 实现本地知识库收集器
  - 实现联网搜索收集器
  - 实现去重和可信度评估
- ✅ 完成素材收集模块测试
  - 80+ 测试用例
  - 100% 功能覆盖
- ✅ 完成素材收集使用示例
  - 7 个完整示例
  - 详细注释说明
- ✅ 完善项目文档
  - 更新 claude.md
  - 创建 6 个文档文件
  - 完成项目统计和分析

### 2026-02-04 (昨日)
- ✅ 完成向量存储模块实现
- ✅ 完成记忆系统集成测试

---

## 🚧 路线规划

### 短期目标 (1-2 周)
- [ ] 设计大纲生成接口
- [ ] 实现基础大纲生成算法
- [ ] 集成素材收集和记忆系统

### 中期目标 (1-2 月)
- [ ] 完成篇章细化模块
- [ ] 实现正文生成引擎原型
- [ ] 添加用户审核接口

### 长期目标 (3-6 月)
- [ ] 完成全文生成引擎
- [ ] 开发 Web 用户界面
- [ ] 性能优化和部署

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](./LICENSE) 文件

---

## 📞 联系方式

- 项目 Issues
- 开发讨论区

---

## 🌟 致谢

感谢所有为这个项目做出贡献的人！

---

**最后更新：** 2026-02-05 14:20 UTC
**项目版本：** 0.2.0
**项目状态：** 🚧 开发中 - 阶段 1 & 2 完成
