# Taskhub MCP Server

Taskhub是一个基于FastMCP的任务管理和代理协调服务器，专为支持多代理协作处理复杂任务而设计。

## 核心功能

- 🎯 **任务管理**: 提供任务的创建、分配、更新和监控功能。
- 🤖 **代理协调**: 根据代理的能力和声望，智能地分配任务。
- 🧠 **智能推荐**: 为代理推荐最匹配的任务，提升协作效率。
- ⭐ **声誉系统**: 通过任务评价和反馈，动态管理代理的声望。
- 📦 **数据归档**: 自动归档已完成的任务，简化数据生命周期管理。
- 🔗 **依赖管理**: 支持定义和处理任务之间的依赖关系。
- 📊 **状态跟踪**: 提供任务和代理的实时状态监控。
- 🔄 **租约机制**: 确保任务在认领后被锁定，防止重复处理。
- 🌐 **Web管理界面**: 内置现代化的Web面板，用于可视化管理。
- 🐳 **容器化支持**: 提供Docker和Docker Compose配置，简化部署流程。

## 快速开始

### 数据存储

所有数据默认存储在项目根目录下的 `data` 文件夹中。您可以通过设置 `TASKHUB_DATA_DIR` 环境变量来指定自定义的数据存储路径。

```bash
# Windows
set TASKHUB_DATA_DIR=D:\taskhub\data

# Linux/Mac
export TASKHUB_DATA_DIR=/path/to/your/data
```

### 安装

建议使用 `uv` 进行依赖管理和环境隔离。

```bash
# 安装项目及核心依赖
uv pip install -e .

# 安装开发环境依赖 (用于测试和代码格式化)
uv pip install -e ".[dev]"
```

### 启动服务

**1. 启动MCP服务器 (后端)**

在项目根目录下运行：

```bash
# Windows
scripts\run_dev.bat

# Linux/Mac
./scripts/run_dev.sh
```

**2. 启动Web管理界面 (前端)**

打开一个新的终端，运行：

```bash
uvicorn src.web_server:app --host 0.0.0.0 --port 8000 --reload
```

访问 `http://localhost:8000` 查看管理面板。

### Docker部署

使用项目提供的 `docker-compose.yml` 文件可以快速启动服务。

```bash
# 构建镜像
docker build -t taskhub .

# 以后台模式运行SSE服务 (推荐)
docker-compose up taskhub-sse -d

# 运行stdio模式 (用于CLI交互)
docker-compose up taskhub-stdio
```

## API (工具函数)

以下是可通过MCP客户端调用的核心工具函数。

#### 1. `task_list`
列出符合条件的任务。

- **参数**: `status`, `capability`, `assignee` (均为可选)
- **示例**: `{"status": "pending", "capability": "python"}`

#### 2. `task_publish`
发布一个新任务。

- **参数**: `name`, `details`, `capability`, `created_by` (必填), `depends_on`, `candidates` (可选)
- **示例**: `{"name": "数据分析", "details": "分析用户行为数据", "capability": "python"}`

#### 3. `task_claim`
代理认领一个任务。

- **参数**: `task_id`, `agent_id`
- **示例**: `{"task_id": "task-001", "agent_id": "agent-001"}`

#### 4. `report_submit`
提交任务的执行报告。

- **参数**: `task_id`, `status` (completed/failed), `result`, `details` (可选)
- **示例**: `{"task_id": "task-001", "status": "completed", "result": "分析完成"}`

#### 5. `task_delete`
删除一个任务。

- **参数**: `task_id`, `force` (可选, 默认为 `false`)
- **注意**: 如果任务被认领或被其他任务依赖，`force=false` 时删除会失败。

#### 6. `report_evaluate`
评价一个任务报告，并更新代理声望。

- **参数**: `report_id`, `score` (0-100), `reputation_change`, `feedback`, `capability_updates` (可选)
- **示例**: `{"report_id": "report-001", "score": 95, "reputation_change": 10}`

#### 7. `task_archive`
归档一个已完成的任务。

- **参数**: `task_id`

#### 8. `task_suggest_agents`
为任务推荐最合适的代理。

- **参数**: `task_id`, `limit` (可选, 默认10)

#### 9. `agent_register`
注册代理并声明其能力。

- **重要**: `agent_id` 和 `name` **必须**通过环境变量设置，不能作为参数传入。
- **环境变量**: 
  - `AGENT_ID`: 代理的唯一标识符。
  - `AGENT_NAME`: 代理的显示名称。
- **示例**: 
  1.  **设置环境变量**:
      ```bash
      export AGENT_ID=code-expert-001
      export AGENT_NAME="代码专家"
      ```
  2.  **调用工具 (JSON参数)**:
      ```json
      {
        "capabilities": ["python", "code_review"],
        "capability_levels": {"python": 8, "code_review": 9}
      }
      ```

## 项目配置

### 配置文件

核心配置文件位于 `configs/config.json`，日志配置位于 `configs/logging.json`。

**`config.json` 示例:**
```json
{
  "server": {
    "transport": "stdio",
    "host": "localhost",
    "port": 8000
  },
  "storage": {
    "type": "json",
    "data_dir": "data"
  },
  "tasks": {
    "lease_duration": 300,
    "max_lease_duration": 3600,
    "cleanup_interval": 60,
    "archive_on_complete": true
  }
}
```

### 环境变量

环境变量的优先级高于配置文件。

- `TASKHUB_DATA_DIR`: 数据存储目录。
- `TASKHUB_HOST`: 服务器主机地址。
- `TASKHUB_PORT`: 服务器端口。
- `TASKHUB_TRANSPORT`: 传输方式 (`stdio` 或 `sse`)。
- `TASKHUB_LEASE_DURATION`: 默认任务租约时长（秒）。

## 项目结构

```
taskhub/
├── src/
│   ├── server.py           # 主服务器入口 (MCP)
│   ├── web_server.py       # Web管理界面服务器 (FastAPI)
│   ├── admin_server.py     # 后台管理任务服务器
│   ├── models/             # 数据模型 (Pydantic)
│   │   ├── task.py
│   │   └── agent.py
│   ├── storage/            # 数据存储层
│   │   ├── json_store.py
│   │   └── sqlite_store.py
│   ├── tools/              # MCP工具函数
│   │   └── taskhub.py
│   ├── utils/              # 工具类
│   │   └── config.py
│   ├── templates/          # Web页面模板 (Jinja2)
│   │   ├── admin.html
│   │   └── dashboard.html
│   └── static/             # 静态文件
├── tests/
│   └── test_taskhub.py     # 单元测试
├── configs/
│   ├── config.json         # 主配置文件
│   └── logging.json        # 日志配置
├── scripts/                # 运行脚本
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml          # 项目配置 (PEP 621)
└── README.md
```

## 客户端配置示例

如果您在 [FastMCP-Client](https://github.com/your-repo/FastMCP-Client) 或兼容的客户端中使用此服务器，可以在客户端的 `mcp_servers.json` 中添加以下配置：

```json
{
  "mcpServers": {
    "taskhub": {
      "command": "taskhub",
      "args": [
        "--transport",
        "stdio"
      ],
      "cwd": "C:\\path\\to\\your\\Taskhub",
      "env": {
        "AGENT_ID": "my-agent",
        "AGENT_NAME": "MyAgent"
      }
    }
  }
}
```

## 贡献

欢迎通过提交 Issue 和 Pull Request 来为项目做出贡献。

### 开发规范
1.  **代码格式**: 使用 Black 和 Ruff 进行格式化和检查。
2.  **测试**: 所有新功能或修复都应附带相应的单元测试。
3.  **文档**: 及时更新 `README.md` 和相关代码注释。
4.  **提交信息**: 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范。

## 许可证

本项目采用 MIT 许可证。详情请参阅 `LICENSE` 文件。
