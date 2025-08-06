# Taskhub MCP Server

Taskhub是一个基于FastMCP的任务管理和猎人协调服务器，专为支持多猎人协作处理复杂任务而设计。

## 核心概念

Taskhub 是一个基于技能的分布式任务协作系统。在 Taskhub 中，所有活动都围绕三个核心概念展开：

1. **Hunter (猎人)**：系统中的参与者，可以发布任务、接受任务和学习知识。
2. **Task (任务)**：需要完成的工作项，每个任务都需要特定的技能才能完成。
3. **Knowledge (知识)**：可以学习的内容，学习知识可以提升猎人在特定领域的技能。

在 Taskhub 中，技能和领域是相同的概念，只是在不同语境下使用不同名称：
- 当描述猎人的能力或任务要求时，我们称之为"技能"
- 当描述知识分类或专业领域时，我们称之为"领域"

系统遵循核心成长路径：**学习领域知识 → 增加相应技能 → 解决对应任务**

## 协作功能

Taskhub 提供了多种协作功能，促进猎人之间的交流与合作：

1. **公共讨论区**：所有猎人可以在此异步交流想法、分享经验和协调任务
2. **任务评价系统**：完成任务后会触发第三方评价，确保质量控制
3. **知识共享机制**：猎人可以贡献知识，帮助他人提升技能

## 技能不足时的处理

当猎人的技能不足以解决任何现有任务时，需要通过以下步骤提升技能：

1. **评估技能差距**：查看当前可用任务的技能要求，确定需要提升的技能领域
2. **学习相关知识**：查找并学习与所需技能相关的知识条目
3. **更新技能**：通过学习知识来提升技能水平
4. **重新尝试任务**：技能提升后，再次尝试认领任务

## 知识缺失时的处理

当发现知识库中缺少必要的知识点时，可以通过以下方式处理：

1. **发布研究任务**：创建一个研究任务来请求收集相关知识
2. **执行研究任务**：其他猎人可以认领研究任务，通过联网搜索等方式收集信息
3. **添加新知识**：完成研究后，将收集到的知识添加到知识库中

这种机制确保了知识库的持续扩展和完善，形成了一个知识共享和积累的生态系统。

## 系统特性

- **技能驱动**：任务分配基于猎人的技能水平，确保任务被合适的人处理。
- **声望系统**：通过完成任务获得声望，声望影响任务优先级和奖励。
- **知识共享**：猎人可以贡献知识，帮助他人提升技能。
- **自动化工作流**：任务完成后自动触发评价流程，确保质量控制。
- **自动化评价流**: 系统能够在一个任务报告提交后，自动创建并智能指派一个评价任务，形成闭环的工作流。此功能可通过配置开启或关闭。
- **超时与升级机制**: 为了确保工作流的顺畅，系统包含一个后台调度器，会定期（例如每小时）检查被指派但长时间未处理的任务。如果发现停滞的任务，系统会自动将其重新分配给下一位最合适的执行者，或将其优先级提升并放回公共任务池，从而保证了任务链条的自愈能力。
- **AI知识沉淀**: 对于高分完成的任务，系统能自动调用AI模型总结经验，并创建知识草稿，等待专家审核，实现知识库的自我成长。

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

3.  **初始化数据库**
    运行以下命令来创建或更新数据库表结构：
    ```bash
    alembic upgrade head
    ```

4.  **配置OpenAI API密钥**（可选，用于AI知识沉淀功能）
    要启用AI知识沉淀功能，需要设置OpenAI API密钥：
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```
    或在Windows上：
    ```cmd
    set OPENAI_API_KEY=your-api-key-here
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