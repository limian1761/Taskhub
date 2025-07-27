# Taskhub MCP Server

基于FastMCP的任务管理和代理协调服务器，支持多代理协作处理任务。

## 功能特性

- 🎯 **任务管理**: 创建、分配、更新和监控任务
- 🤖 **代理协调**: 智能任务分配给合适的代理
- 🧠 **智能推荐**: 基于能力和声望的任务匹配系统
- ⭐ **声誉系统**: 任务评价和代理声望管理
- 📦 **数据归档**: 自动任务归档和生命周期管理
- 🔗 **依赖管理**: 支持任务间依赖关系
- 📊 **状态跟踪**: 实时任务状态监控
- 🔄 **租约机制**: 防止任务重复处理
- 🌐 **Web管理界面**: 现代化的可视化管理面板
- 📱 **实时数据**: 自动刷新任务和代理状态
- 🐳 **容器化**: 支持Docker部署

## 快速开始

### 数据存储

所有数据默认存储在当前工作目录下的 `data` 文件夹中：

```
data/
  ├── agents.json  # 代理数据
  ├── tasks.json   # 任务数据
  ├── tasks.db     # SQLite任务数据库
  └── reports.db   # SQLite报告数据库
```

你可以通过以下两种方式自定义数据存储位置：

1. 使用环境变量（推荐）：
```bash
# Windows
set TASKHUB_DATA_DIR=D:\taskhub\data

# Linux/Mac
export TASKHUB_DATA_DIR=/path/to/data
```

2. 修改配置文件 `configs/config.json` 中的 `storage.data_dir` 配置项。

> 注意：环境变量的优先级高于配置文件。

支持的环境变量：
- `TASKHUB_DATA_DIR`: 数据存储目录
- `TASKHUB_HOST`: 服务器主机地址
- `TASKHUB_PORT`: 服务器端口
- `TASKHUB_TRANSPORT`: 传输方式 (stdio/sse)
- `TASKHUB_LEASE_DURATION`: 默认租约时长（秒）
- `TASKHUB_MAX_LEASE`: 最大租约时长（秒）
- `TASKHUB_CLEANUP_INTERVAL`: 清理间隔（秒）

### 安装依赖

```bash
pip install -e .
```

### 开发环境

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 格式化代码
black src/ tests/
ruff check src/ tests/
```

### 配置文件

项目使用JSON格式配置文件：
- `configs/config.json` - 主服务器配置
- `configs/logging.json` - 日志配置

配置文件示例：
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
    "max_retries": 3
  }
}
```

### 启动服务器

#### 本地开发

**1. 启动MCP服务器**

```bash
# Windows
scripts\run_dev.bat

# Linux/Mac
./scripts/run_dev.sh
```

**2. 启动Web管理界面**

```bash
uv run uvicorn src.web_server:app --host 0.0.0.0 --port 8000 --reload
```

然后在浏览器中访问 http://localhost:8000 即可使用管理界面。

#### Docker

```bash
# 构建镜像
docker build -t taskhub .

# 运行SSE模式
docker-compose up taskhub-sse

# 运行stdio模式
docker-compose up taskhub-stdio
```

#### 命令行

**启动MCP服务器：**

```bash
# SSE模式
python -m src.server --transport sse --host 0.0.0.0 --port 8000

# stdio模式
python -m src.server --transport stdio
```

## API 文档

### 工具函数

#### 1. task_list
列出所有任务，支持过滤。

**参数:**
- `status` (可选): 任务状态 (pending, claimed, completed, failed)
- `capability` (可选): 所需能力
- `assignee` (可选): 分配代理ID

**示例:**
```json
{
  "status": "pending",
  "capability": "python"
}
```

#### 2. task_publish
发布新任务。

**参数:**
- `name`: 任务名称
- `details`: 任务详情
- `capability`: 所需能力
- `created_by`: 创建者ID（必填）
- `depends_on`: 依赖任务ID列表（可选）
- `candidates`: 候选代理ID列表（可选）

**示例:**
```json
{
  "name": "数据分析",
  "details": "分析用户行为数据",
  "capability": "python",
  "depends_on": ["data-preprocessing"]
}
```

#### 3. task_claim
代理认领任务。

**参数:**
- `task_id`: 任务ID
- `agent_id`: 代理ID

**示例:**
```json
{
  "task_id": "task-001",
  "agent_id": "agent-001"
}
```

#### 4. report_submit
提交任务报告。

**参数:**
- `task_id`: 任务ID
- `status`: 任务状态 (completed, failed)
- `result`: 任务执行结果
- `details` (可选): 任务执行过程的详细描述

**示例:**
```json
{
  "task_id": "task-001",
  "status": "completed",
  "result": "分析完成，生成报告",
  "details": "使用了pandas进行数据清洗，matplotlib进行可视化分析"
}
```

#### 5. task_delete
删除任务。

**参数:**
- `task_id`: 要删除的任务ID
- `force` (可选): 是否强制删除，即使有依赖关系，默认为false

**示例:**
```json
{
  "task_id": "task-001",
  "force": false
}
```

**注意事项:**
- 如果任务被其他任务依赖，且`force=false`，删除将失败
- 如果任务被代理认领，删除时会自动从代理的当前任务中移除
- 设置`force=true`可以强制删除有依赖关系的任务

#### 6. report_evaluate
评价任务报告。

**参数:**
- `report_id`: 报告ID
- `score`: 评价分数 (0-100)
- `reputation_change`: 声望值变化
- `feedback` (可选): 评价反馈信息
- `capability_updates` (可选): 能力等级更新

**示例:**
```json
{
  "report_id": "report-001",
  "score": 95,
  "reputation_change": 10,
  "feedback": "任务完成质量很高，代码整洁，文档完整",
  "capability_updates": {"python": 2, "devops": 1}
}
```

#### 7. task_archive
归档已完成的任务。

**参数:**
- `task_id`: 要归档的任务ID

**示例:**
```json
{
  "task_id": "task-001"
}
```

#### 8. task_suggest_agents
为代理推荐最匹配的任务，基于能力和声望排序。

**参数:**
- `agent_id`: 代理ID
- `limit` (可选): 返回结果数量限制，默认10

**示例:**
```json
{
  "agent_id": "agent-001",
  "limit": 5
}
```

**返回:**
返回按匹配度排序的任务列表，包含任务详情和匹配评分。

#### 9. agent_register
代理首次注册，声明自身能力和信息。

**参数:**
- `capabilities`: 能力列表
- `capability_levels` (可选): 能力等级映射

**注意:** `agent_id`和`name`必须从环境变量获取，不再支持参数传入

**示例:**

**步骤1：设置环境变量**
```bash
export AGENT_ID=code-review-agent-001
export AGENT_NAME="代码审查专家"
```

**步骤2：注册代理（无需提供agent_id和name）**
```json
{
  "capabilities": ["python", "javascript", "code_review"],
  "capability_levels": {
    "python": 8,
    "javascript": 6,
    "code_review": 7
  }
}
```

**环境变量使用（必须）:**

代理注册现在**必须**通过环境变量配置，不再支持参数传入。

**必需环境变量:**
- `AGENT_ID`: 代理唯一标识符
- `AGENT_NAME`: 代理显示名称

**快速设置:**
```bash
export AGENT_ID=my-special-agent-001
export AGENT_NAME="智能代码助手"
```

**详细配置指南:** 请参考 [ENV_SETUP.md](./ENV_SETUP.md) 文件，其中包含：
- Windows/Linux/macOS 系统配置方法
- Docker 容器配置
- Python 虚拟环境配置
- VS Code 开发环境配置
- 故障排除指南

**返回:**
注册成功返回代理信息，如果代理已存在则更新信息。

## 数据模型

### Task (任务)
- `id`: 唯一标识符
- `name`: 任务名称
- `details`: 任务详情
- `capability`: 所需能力
- `status`: 任务状态
- `assignee`: 分配代理ID
- `lease_id`: 当前租约ID
- `depends_on`: 依赖任务ID列表
- `parent_task`: 父任务ID
- `created_at`: 创建时间
- `updated_at`: 更新时间

### Agent (代理)
- `id`: 唯一标识符
- `name`: 代理名称
- `capabilities`: 能力列表
- `reputation`: 声望分数
- `status`: 代理状态
- `tasks`: 当前任务列表
- `created_at`: 创建时间
- `updated_at`: 更新时间

## 项目结构

```
taskhub/
├── src/
│   ├── __init__.py
│   ├── server.py           # 主服务器入口
│   ├── web_server.py       # Web管理界面服务器
│   ├── models/
│   │   ├── __init__.py
│   │   ├── task.py         # 任务数据模型
│   │   └── agent.py        # 代理数据模型
│   ├── storage/
│   │   ├── __init__.py
│   │   └── json_store.py   # JSON存储实现
│   ├── tools/
│   │   ├── __init__.py
│   │   └── taskhub.py      # 核心MCP工具
│   ├── utils/
│   │   ├── __init__.py
│   │   └── config.py       # 配置管理
│   ├── templates/
│   │   └── dashboard.html  # 管理界面模板
│   └── static/
│       └── css/
│           └── styles.css  # 管理界面样式
├── tests/
│   ├── __init__.py
│   └── test_taskhub.py     # 单元测试
├── configs/
│   ├── config.json         # 主配置文件 (JSON格式)
│   └── logging.json        # 日志配置 (JSON格式)
├── scripts/
│   ├── run_dev.bat         # Windows开发脚本
│   ├── run_dev.sh          # Linux开发脚本
│   ├── run_sse.bat         # Windows SSE模式
│   └── run_stdio.bat       # Windows stdio模式
├── Dockerfile              # Docker镜像配置
├── docker-compose.yml      # Docker Compose配置
├── pyproject.toml          # 项目配置
└── README.md              # 项目文档
```

## 配置

### 配置文件

配置文件位于 `configs/config.yaml`:

```yaml
server:
  host: 0.0.0.0
  port: 8000
  transport: sse

storage:
  type: json
  data_dir: ./data

tasks:
  default_lease_duration: 300  # 5分钟
  max_lease_duration: 3600     # 1小时
  cleanup_interval: 60       # 1分钟
```

### 环境变量

- `TASKHUB_HOST`: 服务器主机
- `TASKHUB_PORT`: 服务器端口
- `TASKHUB_TRANSPORT`: 传输方式
- `TASKHUB_DATA_DIR`: 数据目录

## 部署

### Docker Compose

使用提供的 `docker-compose.yml` 文件：

```bash
# 生产环境
docker-compose up -d taskhub-sse

# 开发环境
docker-compose up taskhub-dev
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: taskhub
spec:
  replicas: 1
  selector:
    matchLabels:
      app: taskhub
  template:
    metadata:
      labels:
        app: taskhub
    spec:
      containers:
      - name: taskhub
        image: taskhub:latest
        ports:
        - containerPort: 8000
        env:
        - name: TASKHUB_TRANSPORT
          value: "sse"
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: taskhub-pvc
```

## 贡献

欢迎提交 Issue 和 Pull Request！

### 开发规范

1. 代码格式：使用 Black + Ruff
2. 测试：所有功能必须有测试覆盖
3. 文档：更新相关文档
4. 提交：遵循 Conventional Commits

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

# 客户端配置
```json
{
  "mcpServers": {
    "taskhub": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\lichao\\OneDrive\\dev\\Taskhub",
        "run",
        "python",
        "-m",
        "src.server",
        "--transport",
        "stdio"
      ],
      "env": {
        "AGENT_ID": "KIMI",
        "AGENT_NAME": "KIMI"
      }
    }
  }
}
```