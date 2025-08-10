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

## Docker 快速启动 (推荐)

使用 Docker Compose 是启动所有服务的推荐方式。

### 1. 环境配置

在项目根目录创建一个 `outline.env` 文件，用于配置 Outline 服务。

```env
# outline.env - Configuration for Outline Service
UTILS_SECRET=CHANGEME_RANDOM_SECRET_STRING_1
SECRET_KEY=CHANGEME_RANDOM_SECRET_STRING_2
URL=http://localhost:9000
POSTGRES_USER=outline
POSTGRES_PASSWORD=outline
POSTGRES_DB=outline
POSTGRES_HOST=outline-postgres
REDIS_URL=redis://outline-redis:6379
```
> **[!] 重要**: 在启动前，您必须将 `CHANGEME...` 的值替换为您自己生成的、长度至少为32位的强随机字符串。

### 2. 启动服务

在项目根目录下打开终端，运行以下命令：

```bash
docker-compose up --build -d
```

此命令将以后台模式构建并启动所有服务。

### 3. 访问服务

服务完全启动后，您可以通过以下地址访问：

-   **Taskhub API 服务 (Web UI)**: `http://localhost:8001`
-   **Taskhub MCP 服务**: `http://localhost:8000`
-   **Outline 知识库**: `http://localhost:9000`

> **注意**: 首次启动后，请务必先访问 Outline 的地址 (`http://localhost:9000`) 来完成初始化设置。

## 本地开发启动

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