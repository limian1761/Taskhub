# Taskhub FastMCP Server

Taskhub是一个基于FastMCP的任务管理和猎人（代理）协调服务器，专为支持多代理协作处理复杂任务而设计。它通过集成的Web界面提供管理功能，并与外部的 [Outline](https://www.getoutline.com/) 知识库协同工作，以实现强大的知识管理。

## 核心架构

Taskhub 现在采用分离的服务架构，将 API 服务和 MCP 服务分别部署，以提高系统的可扩展性和可维护性：

-   **API 服务 (端口 8001)**: 提供 Web 管理界面和 RESTful API
    -   Web 管理界面
    -   RESTful API
    -   后台任务调度
-   **MCP 服务 (端口 8000)**: 专门处理代理工具调用和 SSE 通信
    -   核心的代理工具调用和 SSE 通信能力
-   **外部知识库 (端口 9000)**: 集成 Outline 作为专业的知识管理系统。

## 架构深入：Hunter与知识库的交互流程

为了更好地理解系统的工作方式，以下是当一个Hunter（代理）执行知识库操作（如 `knowledge_add`）时的详细数据流：

1.  **Hunter -> MCP 服务**: Hunter 连接到 MCP 服务 (`:8000`)，并通过 SSE 连接调用一个在 `tools` 模块中定义的工具函数，例如 `knowledge_add`。
2.  **MCP 服务 -> 工具层**: 服务接收到调用请求，并将其分派给 `taskhub.tools.knowledge_tools` 中的相应函数。
3.  **工具层 -> 服务层**: `knowledge_tools` 中的函数作为接口层，它会直接调用 `taskhub.services.knowledge_service` 中对应的业务逻辑函数（因为所有模块都在同一个进程中）。
4.  **服务层 -> SDK层**: `knowledge_service` 在处理业务逻辑时，会实例化一个 `taskhub.sdk.outline_client.OutlineClient`。
5.  **SDK层 -> 知识库服务**: `OutlineClient` 从配置中读取 Outline 服务的 URL (`http://localhost:9000`) 和 API 密钥，然后向其发送一个标准的 HTTP 请求。
6.  **返回响应**: Outline 服务处理请求后，HTTP 响应会沿着调用链原路返回，最终由 MCP 服务通过 SSE 连接传递给 Hunter。

这个分层设计确保了职责的清晰分离：Hunter 无需关心知识库的具体实现，只需与 MCP 提供的“工具”交互即可。

```
+--------+   1. 调用工具 (SSE)   +--------------------------+   2. 分派   +-----------------------+
| Hunter | --------------------> |  MCP 服务 (mcp_server.py)  | --------> | 工具层 (tools)        |
+--------+                      +--------------------------+           +-----------------------+
                                      |         ^                          | 3. 调用服务 (In-Process)
    ^                                 |         |                          v
    | 6. 返回最终结果 (SSE)            |         |                +-----------------------+
    +----------------------------------'         +-------------- | 服务层 (services)     |
                                                                  +-----------------------+
                                                                            | 4. 使用SDK
                                                                            v
                                                                  +-----------------------+
                                                                  | SDK 层 (outline_client) |
                                                                  +-----------------------+
                                                                            | 5. 发送HTTP请求
                                                                            v
                                                                  +-----------------------+
                                                                  | 知识库 (Outline)      |
                                                                  +-----------------------+
```

## 功能特性

-   **技能驱动的任务分配**: 任务与所需技能关联，确保它们被具备相应能力的代理处理。
-   **协作式知识管理**: 通过集成的 Outline，代理可以搜索、创建和共享结构化的知识。
-   **自动化工作流**: 支持任务完成后自动触发评价、超时任务自动升级或重新分配等机制。
-   **Web UI**: 直观的管理界面，用于查看系统状态、任务列表和代理活动。

---

## 使用 Docker 部署 Outline 知识库

本项目包含一个独立的 `docker-compose.yml` 文件，专门用于快速部署 Outline 知识库。

### 1. 环境配置

在项目根目录中，复制或重命名 `outline.env.example` 为 `outline.env`，并根据您的环境修改以下关键配置：

```env
# outline.env - Outline 服务核心配置

# 您的 Outline 实例的公开访问 URL。
# 如果您在本地测试，请使用 http://localhost:9000
# 如果您使用 cpolar 等隧道工具，请使用您的公开域名，例如 http://your-domain.com
URL=http://localhost:9000

# 生成两个强随机密钥，可以使用 `openssl rand -hex 32` 命令生成
SECRET_KEY=CHANGEME_YOUR_RANDOM_SECRET_KEY_1
UTILS_SECRET=CHANGEME_YOUR_RANDOM_SECRET_KEY_2

# 至少配置一种登录方式，否则无法登录 Outline。
# 以 Slack 为例，您需要去 Slack API 控制台创建一个应用，并获取凭证。
SLACK_CLIENT_ID=YOUR_SLACK_CLIENT_ID
SLACK_CLIENT_SECRET=YOUR_SLACK_CLIENT_SECRET

# 如果在本地或没有配置 SSL 的情况下运行，请取消注释此行以禁用 HTTPS
PGSSLMODE=disable
```

> **[!] 重要**:
> *   **必须**配置至少一种登录方式（如 Slack, Google, Microsoft）。
> *   **必须**将 `CHANGEME...` 的值替换为您自己生成的、长度至少为32位的强随机字符串。

### 2. 更新 Slack 应用的重定向 URI

如果您使用 Slack 登录，您必须在 [Slack API 控制台](https://api.slack.com/apps) 中，将您的重定向 URI 添加到应用的 "OAuth & Permissions" -> "Redirect URLs" 中。

这个 URI 必须与您在 `outline.env` 中配置的 `URL` 完全匹配，并以 `/auth/slack.callback` 结尾。例如：
`http://localhost:9000/auth/slack.callback` 或 `http://your-domain.com/auth/slack.callback`

### 3. 启动服务

完成配置后，在项目根目录下运行以下命令：

```bash
docker-compose up -d
```

此命令将以后台模式启动 Outline、PostgreSQL 和 Redis 服务。

### 4. 访问服务

服务启动后，您可以通过在 `outline.env` 中配置的 `URL` 地址（例如 `http://localhost:9000`）来访问您的 Outline 知识库。

---

## 本地开发启动 (Taskhub)

对于本地开发，我们提供了便捷的启动脚本，它会启动分离的 API 服务和 MCP 服务。

1.  **安装依赖**:
    ```bash
    uv venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate    # Windows
    uv pip install -e .[dev]
    ```
2.  **初始化数据库**:
    ```bash
    alembic upgrade head
    ```
3.  **使用脚本启动**:
    -   **Windows**:
        ```cmd
        .\start_all.bat
        ```
    -   **Linux/macOS**:
        ```bash
        chmod +x start_all.sh
        ./start_all.sh
        ```
    脚本将启动两个独立的服务：
    -   API 服务: `http://localhost:8001`
    -   MCP 服务: `http://localhost:8000`

## API (工具函数)

FastMCP 客户端需要连接到 **Taskhub MCP 服务** (默认为 `http://localhost:8000`) 来调用以下工具函数。

-   **任务管理 (`task_tools`)**
-   **代理管理 (`hunter_tools`)**
-   **知识库 (`knowledge_tools`)**
-   **讨论区 (`discussion_tools`)**

## 项目结构

```
.
├── docker-compose.yml      # Docker 编排文件，定义所有服务
├── start_all.bat           # Windows 本地开发启动脚本
└── src/
    └── taskhub/            # 核心 Python 包
        ├── api_server.py   # ✅ API 服务入口 (FastAPI)
        ├── mcp_server.py   # ✅ MCP 服务入口 (FastMCP)
        ├── __main__.py     # CLI 入口
        ├── ...
```