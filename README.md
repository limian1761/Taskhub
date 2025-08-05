# Taskhub MCP Server

Taskhub是一个基于FastMCP的任务管理和猎人协调服务器，专为支持多猎人协作处理复杂任务而设计。

## 核心功能

- 🎯 **任务管理**: 提供任务的创建、分配、更新和监控功能。
- 🤖 **代理协调**: 根据代理的技能 (`skills`) 智能地分配任务。
- 🧠 **知识库 (Knowledge Base)**: 支持创建和管理知识点，允许代理通过学习 (`hunter_study`) 来提升其技能分数。
- ⭐ **技能系统 (Skill System)**: 通过任务评价和主动学习，动态管理代理在各项技能上的熟练度分数。
- 📦 **数据归档**: 自动归档已完成的任务，简化数据生命周期管理。
- 🔗 **依赖管理**: 支持定义和处理任务之间的依赖关系。
- 📊 **状态跟踪**: 提供任务和代理的实时状态监控。
- 📝 **日志系统**: 完整的操作日志记录，便于问题排查和系统监控。
- 🌐 **Web管理界面**: 内置现代化的Web面板，用于可视化管理。
- 🐳 **容器化支持**: 提供Docker和Docker Compose配置，简化部署流程。

## 快速开始

### 环境要求
- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (推荐的包管理器)

### 安装

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your-repo/Taskhub.git
    cd Taskhub
    ```

2.  **安装依赖**
    ```bash
    uv venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate    # Windows
    uv pip install -e .
    ```

### 启动服务

使用项目根目录下的 `start_all.bat` (Windows) 或 `start_all.sh` (Linux/macOS) 脚本一键启动所有服务。

```bash
# Windows
.\start_all.bat

# Linux/macOS
chmod +x start_all.sh
./start_all.sh
```

脚本将启动两个核心服务：
- **主服务 (Taskhub MCP Server)**: 运行在 `http://localhost:3000`。
- **API & Web 服务器**: 运行在 `http://localhost:8000`。

### Web管理界面

启动服务后，在浏览器中访问 `http://localhost:8000` 即可打开Web管理界面。

### 多租户 (Namespace)

API服务器支持通过 `?namespace=` 查询参数来隔离不同项目的数据。

**示例**:
- `http://localhost:8000/api/tasks?namespace=project_x`

### API (工具函数)

以下是可通过MCP客户端调用的核心工具函数。

- `task_publish(name: str, details: str, required_skill: str, ...)`: 发布一个新任务。
- `task_claim(task_id: str)`: 认领一个任务。
- `report_submit(task_id: str, status: str, result: str, ...)`: 提交任务报告。
- `report_evaluate(report_id: str, score: int, feedback: str, skill_updates: dict)`: 评价报告并更新提交者的技能分数。
- `hunter_register(skills: dict)`: 注册自己并声明初始技能。
- `hunter_study(knowledge_id: str)`: 学习一个知识点以提升相关技能分数。
- `knowledge_add(title: str, content: str, skill_tags: list[str], ...)`: 添加一个新的知识点。
- `knowledge_list(skill_tag: str | None)`: 列出知识点。
- `knowledge_search(query: str)`: 搜索知识库。
- `get_system_guide()`: 获取系统操作指南。

## Docker部署

使用 `docker-compose.yml` 文件可以快速启动服务。

```bash
docker-compose up --build -d
```

## 项目结构

```
taskhub/
├── src/
│   ├── api_server.py         # 统一的API和Web服务器
│   ├── taskhub/              # Python包
│   │   ├── server.py         # 主服务器 (MCP)
│   │   ├── models/           # 数据模型
│   │   ├── storage/          # 数据存储
│   │   └── tools/            # 核心逻辑
│   ├── templates/
│   └── static/
├── start_all.bat
├── start_all.sh
...
```

### 计划
✦ 这是一个很好的问题。构建一个高效的知识库是提升任何项目（尤其是像Taskhub这样基于hunter的系统）智能和效率的核心
  。一个“高效”的知识库不仅仅是存储信息，更在于知识的高质量、易于获取、和能够被智能体（hunter）主动、准确地应用
  。

  结合您当前的Taskhub项目，我们可以从以下几个层面来构建一个更高效的知识库：

  1. 知识的结构化与质量 (Structured & High-Quality Knowledge)

  高质量的内容是基础。可以从以下几点入手：
   * 模板化： 为不同类型的知识（如：操作指南、错误排查、最佳实践、代码片段）创建标准模板。这能确保知识的完整性
     和一致性。
   * 富文本与元数据：
     使用Markdown等格式来清晰地组织内容。更重要的是，为每个知识条目添加丰富的元数据（Metadata），例如：
       * domain_tags: (您已有的) 领域标签，非常重要。
       * task_relevance: 关联的任务类型。
       * author/owner: 知识负责人。
       * created_at/updated_at: 创建/更新日期。
       * confidence_score: 知识的置信度。
       * usage_count: 使用频率。
   * 版本控制： 知识也需要像代码一样进行版本管理，方便追踪变更和回滚。

  2. 知识的获取与输入 (Acquisition & Input)

  让知识录入变得简单、甚至自动化：
   * 自动化沉淀： Taskhub的核心是任务执行。可以设计一个机制，在任务成功完成后，让hunter自动总结本次任务的关键步
     骤、解决方案，并格式化为知识库条目，交由人类审核后入库。
   * 多渠道输入： 除了手动调用knowledge.add，可以开发插件或接口，从其他系统（如Git提交信息、Slack对话、技术文
     档）中提取和导入知识。

  3. 核心：知识的检索与应用 (Retrieval & Application)

  这是最能体现“高效”的地方。传统的关键词搜索已经不够用了。

  我强烈建议引入语义搜索（Semantic Search）和检索增强生成（Retrieval-Augmented Generation, RAG）流程。

  这是当前大语言模型应用中最核心的技术之一，能让知识库的效能产生质的飞跃。

  基本思路如下：

   1. 知识向量化 (Embedding)：
       * 当一个知识条目被创建或更新时，使用一个深度学习模型（Embedding
         Model）将其内容（标题、正文等）转换成一个数学向量（Vector）。
       * 这个向量可以被认为是该知识在多维空间中的“语义坐标”。
       * 所有知识条目的向量存储在一个专门的向量数据库中（如FAISS, ChromaDB, Pinecone等）。

   2. 语义检索 (Semantic Retrieval)：
       * 当一个hunter接到一个新任务时，它不再是去知识库里做关键词搜索。
       * 而是先将任务描述也用同一个Embedding Model转换成一个查询向量（Query Vector）。
       * 然后，在向量数据库中，计算这个查询向量与所有知识向量的“距离”（通常是余弦相似度）。
       * 距离最近的N个知识条目，就是与当前任务语义上最相关的知识。

   3. 检索增强生成 (RAG)：
       * hunter拿到这N个最相关的知识条目后，将它们作为上下文（Context），连同原始的任务指令，一起发送给大语言模
         型（LLM）。
       * 这样，LLM就能基于这些“背景知识”来完成任务，而不是凭空猜测。这极大地提高了任务完成的准确性和可靠性。

  4. 知识的维护与演进 (Maintenance & Evolution)

  知识库需要持续迭代：
   * 反馈闭环： hunter在使用完一个知识后，可以对其进行“评价”。比如，如果应用该知识后任务成功，则增加该知识的con
     fidence_score和usage_count；如果失败，则降低分数，并触发审查流程。
   * 定期审查： 对于长期未使用或评分较低的知识，应有机制定期提醒owner进行审查、更新或归档。
   * 发现“知识缺口”： 分析那些hunter无法从知识库中找到相关信息的任务。这些失败的查询记录本身就是宝贵的数据，它
     们指明了知识库需要补充哪些内容。

  ---

  针对Taskhub项目的具体建议

  我可以协助您将上述理念落地到您的项目中。我们可以从实现一个基础的RAG流程开始：

   1. 分析现有代码： 我需要先阅读一下taskhub/models, taskhub/storage,
      taskhub/tools下的相关代码，了解当前知识库的数据模型和存储方式。
   2. 改造知识模型： 在taskhub.models中，为知识模型增加embedding字段。
   3. 实现向量化和存储： 改造taskhub.knowledge.add工具，在添加知识时，调用一个开源的Embedding模型（例如sentence
      -transformers库中的模型）生成向量，并将其存入数据库。
   4. 创建语义搜索工具： 创建一个新的工具，如taskhub.knowledge.semantic_search(query:
      str)，它能接收一个查询，将其向量化，并返回最相关的知识。
   5. 整合到hunter工作流：
      修改hunter执行任务的逻辑，在处理任务前，先调用semantic_search获取背景知识，然后再进行后续操作。