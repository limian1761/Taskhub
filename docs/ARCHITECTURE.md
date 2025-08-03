# GeometryMaster 平台 - Taskhub 服务详细设计文档

**版本:** 2.2
**更新说明:** 新增报告列表功能，支持查看报告评价结果
**日期:** 2025年7月27日
**变更摘要:** 在v2.0架构定义的基础上，补充了程序框架的容器化构建细节，包括示例Dockerfile和完善的docker-compose.yml，使设计文档成为可直接执行的蓝图。

## 目录
1.  [引言](#1-引言)
2.  [设计哲学与核心原则](#2-设计哲学与核心原则)
3.  [系统架构 (v2.0)](#3-系统架构-v20)
4.  [数据模型 (v2.0)](#4-数据模型-v20)
5.  [MCP 工具集 API 详述 (v2.0)](#5-mcp-工具集-api-详述-v20)
6.  [客户端集成策略](#6-客户端集成策略)
7.  [核心机制：并发控制与任务租约](#7-核心机制并发控制与任务租约)
8.  [高级机制 1：工作流自动化 (DAG)](#8-高级机制-1工作流自动化-dag)
9.  [高级机制 2：数据生命周期管理](#9-高级机制-2数据生命周期管理)
10. [高级机制 3：代理自主性与子任务](#10-高级机制-3代理自主性与子任务)
11. [核心工作流示例 (v2.0)](#11-核心工作流示例-v20)
12. [部署与扩展性](#12-部署与扩展性)
13. [建议程序框架 (Proposed Program Framework)](#13-建议程序框架-proposed-program-framework)
14. [附录 A: 任务分类枚举](#14-附录-a-任务分类枚举)
15. [附录 B: 任务优先级枚举](#15-附录-b-任务优先级枚举)
16. [附录 C: 预先定义的能力矩阵](#16-附录-c-预先定义的能力矩阵)

---

### 1. 引言
本文档定义了`Taskhub`服务 v2.0 的技术架构与设计。此版本在前一版的基础上进行了重大升级，旨在解决长期运行的扩展性问题，并引入了高级自动化与智能机制，为`GeometryMaster`平台构建一个更健壮、更智能的未来。

### 2. 设计哲学与核心原则
v2.0 继承并强化了原有的核心原则：
*   **协议驱动 (Protocol-Driven)**
*   **状态原子性 (State Atomicity)**
*   **逻辑与传输解耦 (Logic/Transport Decoupling)**
*   **(新增) 服务解耦与可扩展性 (Service Decoupling & Scalability)**
*   **(新增) 智能匹配与声誉系统 (Intelligent Matching & Reputation System)**

### 3. 系统架构 (v2.0)

为提升系统的鲁棒性和可扩展性，原单体`Taskhub`服务被解耦为两个独立的微服务。

#### 3.1. 架构图 (v2.0)

```text
+---------------------------------+      +---------------------------------+
|   MCP 主机 (e.g., Gemini CLI)   |      | MCP 客户端 (e.g., Cursor, Agent) |
+---------------------------------+      +---------------------------------+
                 |                                      |
                 |       (JSON-RPC 2.0 over HTTP)       |
                 +-----------------+--------------------+
                                   |
                                   v
+--------------------------------------------------------------------------+
|                             Taskhub-API                                  |
|                 (Stateless, Real-time MCP Server)                        |
|                     (包含写锁、工具执行引擎、数据访问层)                     |
+--------------------------------------------------------------------------+
     ^
     | (MCP Tool Calls, e.g., task_list, report_submit)
     |
+--------------------------------------------------------------------------+
|                           Taskhub-Scheduler                              |
|                    (Stateful, Background Worker)                         |
|  - 定时检查并释放过期的任务租约                                              |
|  - 定时归档已完成的旧任务                                                  |
+--------------------------------------------------------------------------+
     |
     | (Read/Write)
     v
+--------------------------------------------------------------------------+
|                            Data Storage                                  |
| - taskhub_active.json (for active tasks)                                 |
| - taskhub_archive.db (SQLite for archived tasks)                         |
+--------------------------------------------------------------------------+
```

#### 3.2. 组件说明
*   **Taskhub-API**: 一个无状态、轻量级的实时MCP服务器。它的唯一职责是处理来自主机和客户端的工具调用请求。它包含了并发写锁和核心工具执行引擎。
*   **Taskhub-Scheduler**: 一个独立的后台工作进程。它负责所有时间驱动的、异步的维护任务，通过调用`Taskhub-API`的工具来完成工作，扮演着“系统管家”的角色。

### 4. 数据模型 (v2.0)

#### 4.1. `tasks` 对象模型
为支持DAG和子任务，`tasks`对象模型进一步扩展。

```json
{
  "id": "task-b7a4-4f1c",
  "parent_task_id": "task-a1b2-3c4d",
  "depends_on": ["task-e5f6-7g8h"],
  "name": "实现点云体素格降采样算法",
  "details": "...",
  "capability": "data-processing-downsample",
  "category": "Feature",
  "priority": "High",
  "status": "pending",
  "assignee": null,
  "lease_id": null,
  "lease_expires_at": null,
  "output": null,
  "created_at": "2025-07-26T15:00:00Z",
  "updated_at": "2025-07-26T15:00:00Z",
  "history": []
}
```

*   **parent_task_id** `[String]` 可选, 父任务的ID。用于标识此任务是由哪个任务分解而来的子任务。
*   **depends_on** `[Array<String>]` 可选, 前置依赖任务的ID数组。此任务只有在所有依赖项都完成后才能开始。
*   **status** `[String]` 必需, 状态枚举增加 `"archived"`。

#### 4.2. `agents` 对象模型
`agents` 对象定义了系统中的一个代理（赏金猎人）。

```json
{
  "id": "hunter-alpha",
  "capabilities": [
    "data-analysis",
    "research-library-evaluate"
  ],
  "proven_capabilities": [
    "data-analysis"
  ],
  "reputation": 150,
  "created_at": "2025-07-27T10:00:00Z",
  "updated_at": "2025-07-27T12:30:00Z"
}
```
*   **id** `[String]` 必需, 代理的唯一标识符。
*   **capabilities** `[Array<String>]` 必需, 代理声称自己拥有的能力列表。
*   **proven_capabilities** `[Array<String>]` 必需, 代理已经成功完成并通过验证的能力列表。
*   **reputation** `[Integer]` 必需, 代理的声望值，通过完成任务获得。
*   **created_at** `[String]` 必需, 代理首次注册的时间戳 (ISO 8601)。
*   **updated_at** `[String]` 必需, 代理信息最后更新的时间戳 (ISO 8601)。

### 5. MCP 工具集 API 详述 (v2.0)
Taskhub 通过一个统一的 `JSON-RPC 2.0` 端点提供服务。所有请求都应包含 `agent_id` 以进行身份识别。

#### **`task_suggest_agents`**
智能任务推荐系统，为代理推荐最匹配的任务。

*   **目的**: 基于代理的能力、声望、任务优先级和创建时间，为代理智能推荐最适合的任务。
*   **核心算法**:
    1.  获取所有待处理任务（status=pending）
    2.  检查任务依赖关系，确保所有依赖任务已完成
    3.  根据代理能力匹配任务所需能力
    4.  计算匹配评分：
        - 能力匹配度 (权重: 0.4)
        - 代理声望 (权重: 0.3)
        - 任务优先级 (权重: 0.2)
        - 任务创建时间 (权重: 0.1)
    5.  按评分降序排序，返回最佳匹配任务
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "hunter-alpha",
      "limit": 5
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "tasks": [
        {
          "task": { ... }, // 完整任务对象
          "score": 85.5,   // 匹配评分
          "reason": "高能力匹配度 + 优秀声望"
        },
        { ... }
      ]
    }
    ```

#### **`report_evaluate`**
评价任务报告，更新代理声望和能力记录。

*   **目的**: 建立任务质量反馈机制，提升代理声誉系统的准确性。
*   **核心逻辑**:
    1.  验证报告对应的任务状态为"completed"
    2.  记录评价分数和反馈
    3.  更新代理声望：
       - 高分评价增加声望
       - 低分评价降低声望
    4.  更新代理的"proven_capabilities"记录
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "evaluator-bot",
      "report_id": "report-xyz",
      "score": 95,
      "reputation_change": 10,
      "feedback": "代码质量优秀，文档完整",
      "capability_updates": {
        "csharp": 8
      }
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "evaluated",
      "report": { ... },
      "agent": { ... } // 更新后的代理对象
    }
    ```

#### **`task_archive`**
归档已完成的任务到长期存储。

*   **目的**: 实现数据生命周期管理，保持活跃数据库性能。
*   **核心逻辑**:
    1.  验证任务状态为"completed"或"failed"
    2.  将任务从活跃存储移动到归档存储
    3.  更新任务状态为"archived"
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "system-scheduler",
      "task_id": "task-old-001"
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "archived",
      "task_id": "task-old-001"
    }
    ```

---

#### **`agent_register`**
注册一个新的代理或更新现有代理的信息。

*   **目的**: 声明一个代理的存在，并告知系统其具备的能力。
*   **注意**: `agent_id`和`name`将从环境变量中获取，不再通过参数传递
    *   环境变量`AGENT_ID`：代理的唯一标识符
    *   环境变量`AGENT_NAME`：代理的显示名称
*   **参数 (`params`)**:
    ```json
    {
      "capabilities": ["data-analysis", "research-library-evaluate"],
      "capability_levels": {
        "data-analysis": 8,
        "research-library-evaluate": 6
      }
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "success",
      "agent": { ... } // 返回完整的 agent 对象
    }
    ```
*   **核心逻辑**:
    1.  如果代理ID已存在，则更新其能力信息
    2.  新代理初始声望为0
    3.  支持声明多个能力和对应的能力等级

---

#### **`task_list`**
列出当前可用的任务。

*   **目的**: 允许代理发现可以认领的任务。
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "hunter-alpha",
      "status": "pending", // 必需, 过滤任务状态
      "capability": "data-analysis" // 可选, 按能力过滤
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "tasks": [
        { ... }, // 任务对象1
        { ... }  // 任务对象2
      ]
    }
    ```

---

#### **`task_publish`**
创建一个新任务。

*   **目的**: 允许主机或有权限的代理发布新任务。
*   **参数 (`params`)**:
    ```json
    {
      "name": "Analyze user engagement",
      "details": "Analyze the provided dataset to find user engagement trends.",
      "capability": "data-analysis",
      "created_by": "creator-id",  // 必填：创建者的ID
      "depends_on": [],            // 可选：依赖的任务ID列表
      
      "parent_task_id": "task-abc", // 可选
      "depends_on": ["task-123"]   // 可选
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "created",
      "task": { ... } // 返回新创建的完整 task 对象
    }
    ```

---

#### **`task_claim`**
认领一个可用的任务。

*   **目的**: 让代理获得一个任务的所有权和执行权。
*   **核心逻辑**:
    1.  系统会查找 `status` 为 `pending` 的任务。
    2.  检查任务的 `depends_on` 列表，确保所有依赖任务都已 `completed`。
    3.  如果指定了 `capability`，则只在匹配该能力的可用任务中选择。
    4.  在所有符合条件的任务中，选择 `priority` 最高的那个分配给代理。
    5.  分配成功后，任务状态变为 `in_progress`，并设置 `assignee`, `lease_id`, 和 `lease_expires_at`。
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "hunter-alpha",
      "capability": "data-analysis" // 必需, 声明使用哪种能力来认领
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "claimed",
      "task": { ... } // 返回被认领的完整 task 对象
    }
    ```
*   **失败返回 (`error`)**: 如果没有符合条件的任务，将返回一个错误。

---

#### **`report_submit`**
提交任务结果或报告任务失败。

*   **目的**: 提交任务成果，或报告任务失败。
*   **核心逻辑**:
    *   **完成门控**: 当 `status` 更新为 `completed` 时，系统会检查该任务的所有子任务是否都已完成。如果存在未完成的子任务，操作将被拒绝。
*   **参数 (`params`)**:
    ```json
    {
      "agent_id": "hunter-alpha",
      "task_id": "task-xyz", // 必需, 要更新的任务ID
      "status": "completed", // 必需, 新状态: "completed" 或 "failed"
      "output": "User engagement has increased by 15%." // 任务产出
    }
    ```
*   **成功返回 (`result`)**:
    ```json
    {
      "status": "updated",
      "task": { ... } // 返回更新后的完整 task 对象
    }
    ```

### 6. 配置管理与环境变量

Taskhub 采用分层配置管理策略，支持通过配置文件和环境变量来自定义服务行为。

#### 6.1. 配置优先级
配置项的优先级从高到低为：
1. 环境变量
2. 配置文件 (`configs/config.json`)
3. 代码默认值

#### 6.2. 环境变量配置
支持以下环境变量：
```bash
# 数据存储
TASKHUB_DATA_DIR     # 数据目录路径

# 服务器配置
TASKHUB_HOST         # 服务器主机地址
TASKHUB_PORT         # 服务器端口
TASKHUB_TRANSPORT    # 传输方式 (stdio/sse)

# 任务管理
TASKHUB_LEASE_DURATION    # 默认租约时长（秒）
TASKHUB_MAX_LEASE        # 最大租约时长（秒）
TASKHUB_CLEANUP_INTERVAL # 清理间隔（秒）
```

#### 6.3. 配置文件结构
`configs/config.json` 的标准结构：
```json
{
  "server": {
    "host": "localhost",
    "port": 8000,
    "transport": "stdio"
  },
  "storage": {
    "type": "json",
    "data_dir": "data"
  },
  "task": {
    "default_lease_duration": 30,
    "max_lease_duration": 120,
    "cleanup_interval": 300
  }
}
```

### 7. 客户端集成策略
客户端与 Taskhub 服务的集成遵循标准的、无状态的协议，以保证最大的灵活性和兼容性。

*   **协议**: `JSON-RPC 2.0` over `HTTP POST`。
*   **端点**: 所有请求都发送到单一的 `mcp` 端点 (例如 `http://localhost:8080/mcp`)。
*   **认证**: 采用无状态的 `agent_id` 认证。**每个** RPC 请求的 `params` 对象中都**必须**包含发起该请求的代理 `agent_id` 字段。服务器根据此 ID 来识别调用者身份并验证权限。
*   **推荐库**: 强烈建议客户端使用实现了 MCP 协议的官方或第三方 SDK (如 `@modelcontextprotocol/sdk` for JS/TS) 来处理通信细节，而不是手动构建 HTTP 请求。

#### 请求-响应示例
一个典型的 `task_list` 调用流程如下：

**--> 客户端请求 (POST /mcp)**
```http
POST /mcp HTTP/1.1
Host: localhost:8080
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "task_list",
  "params": {
    "agent_id": "hunter-alpha",
    "status": "pending"
  },
  "id": "req-1"
}
```

**<-- 服务器响应**
```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "result": {
    "tasks": [
      {
        "id": "task-456",
        "name": "Analyze user engagement",
        "status": "pending",
        ...
      }
    ]
  },
  "id": "req-1"
}
```

### 7. 核心机制：并发控制与任务租约
为确保在多代理并发操作下的数据一致性和任务执行的可靠性，Taskhub 依赖两大核心机制。

#### 7.1. 并发控制
由于 `Taskhub-API` 服务本身是无状态的，多个实例可能被同时部署。此外，`Taskhub-Scheduler` 也会在后台对数据进行读写。这些并发操作使得对共享数据源（`taskhub_active.json`）的访问控制至关重要。

*   **机制**: 任何对 `taskhub_active.json` 的**写操作**（创建、更新、删除任务）都必须获取一个**文件锁**。
*   **实现**: 在执行写操作前，`Taskhub-API` 实例必须先成功获取对 `taskhub_active.json.lock` 文件的独占锁。操作完成后，立即释放该锁。这确保了同一时刻只有一个进程可以修改主数据文件，从而避免了数据损坏和竞态条件。

#### 7.2. 任务租约 (Task Leasing)
任务租约机制旨在防止任务被代理认领后，因代理宕机或失联而被永久锁定，无法被再次执行。

*   **租约生命周期**:
    1.  **获取**: 当一个代理成功调用 `task_claim` 时，`Taskhub-API` 会为该任务生成一个唯一的 `lease_id`，并计算一个未来的 `lease_expires_at` 时间戳（例如，当前时间 + 30分钟）。这些信息连同 `assignee`（代理ID）一起被写入任务对象。
    2.  **执行**: 代理必须在租约到期前完成任务，并通过 `report_submit` 提交结果。成功的更新会清除租约信息。
    3.  **过期与释放**: `Taskhub-Scheduler` 服务中的 `lease_manager` 作业会定期（例如，每分钟）扫描所有 `in_progress` 状态的任务。
    4.  如果发现某个任务的 `lease_expires_at` 时间戳已早于当前时间，调度器会认为该租约已过期。
    5.  调度器会将该任务的状态重置回 `pending`，并清空 `assignee`, `lease_id`, `lease_expires_at` 字段。
*   **结果**: 任务被安全地释放回任务池，可供其他代理重新认领，保证了系统的健壮性和任务流的持续进行。

### 8. 高级机制 1：工作流自动化 (DAG)
*   **问题**: 手动按顺序创建和管理有依赖关系的任务，流程繁琐且易出错。
*   **解决方案**: 通过`depends_on`字段将任务链接成有向无环图(DAG)。
    *   `Taskhub`平台现在可以理解任务间的依赖关系。`task_claim`的智能过滤确保了任务总是按正确的顺序被执行。这使得复杂的、多步骤的工作流可以被一次性定义，然后由代理们自动、有序地完成。

### 9. 高级机制 2：数据生命周期管理
*   **问题**: 单个JSON文件随时间推移会无限增大，导致性能下降。
*   **解决方案**: 实施数据分层与归档策略。
    *   **活跃数据**: `taskhub_active.json`只存储进行中的任务。
    *   **归档数据**: `taskhub_archive.db` (推荐使用SQLite) 用于存储所有终态（`completed`, `cancelled`等）的旧任务。
    *   **自动化归档**: `Taskhub-Scheduler`服务会定期运行一个归档作业，将`Taskhub-API`中符合归档条件的任务移动到归档数据库中，保持活跃数据库的轻量和高效。

### 10. 高级机制 3：代理自主性与子任务
*   **问题**: 代理只是被动的任务执行者，无法应对超出预设粒度的复杂任务。
*   **解决方案**: 允许代理通过调用`task_publish`来创建子任务。
    *   **分而治之**: 代理在执行一个复杂任务时（如`实现点云处理模块`），可以将其分解为更小的、可管理的子任务（如`子任务1: 解析E57`，`子任务2: 实现滤波算法`），并为这些子任务设置正确的`capability`。
    *   **涌现式协作**: 一个代理创建的子任务可以被其他更专业的代理认领，从而实现代理间的动态、自主协作。
    *   **完成门控**: 父任务的完成状态与其所有子任务的完成状态绑定，确保了工作的完整性。

### 11. 核心工作流示例 (v2.0)
一个包含依赖和子任务的复杂功能开发流程：
1.  **定义工作流 (Host)**: `Gemini`一次性发布三个任务：
    *   T1: `{ name: "研究点云压缩库", capability: "research-library-evaluate" }`
    *   T2: `{ name: "实现压缩功能", capability: "dev-csharp-implement", depends_on: ["T1"] }`
    *   T3: `{ name: "编写压缩功能测试", capability: "qa-test-unit", depends_on: ["T2"] }`
2.  **研究 (Client)**: 只有T1是可认领的。`KIMI`代理`claim`并完成了T1。
3.  **实现与分解 (Client)**: T1完成后，T2变为可认领状态。`Lingma`代理`claim`了T2。在实现过程中，`Lingma`发现需要一个独立的性能测试，于是她创建了一个子任务：
    *   T2.1: `{ name: "基准测试新算法", parent_task_id: "T2", capability: "research-performance-benchmark" }`
4.  **并行协作**: `KIMI`代理发现了新的研究任务T2.1，并`claim`执行。同时`Lingma`继续T2的其他编码工作。
5.  **完成与解锁**: `KIMI`完成T2.1。`Lingma`完成T2的编码后，尝试将T2标记为`completed`，但因为其子任务T2.1早已完成，操作成功。T2的完成解锁了T3。
6.  **测试**: QA代理`claim`并完成了T3，整个工作流结束。

### 12. 部署与扩展性
*   **部署**: v2.0架构推荐使用Docker Compose进行部署，可以轻松地同时启动和管理`Taskhub-API`和`Taskhub-Scheduler`两个服务。
*   **扩展性**:
    *   **无状态API**: `Taskhub-API`是无状态的，可以轻松地水平扩展（即运行多个实例）来应对高并发请求。
    *   **独立工作进程**: `Taskhub-Scheduler`可以根据后台任务的负载进行独立的垂直或水平扩展。

---

### 13. 建议程序框架 (Proposed Program Framework - Python版本)
此框架基于Python语言特性，采用FastMCP框架构建，支持stdio和SSE两种传输方式，提供轻量级、可扩展的MCP服务器架构。

#### 13.1. 顶层目录结构

基于Python的MCP服务器架构，采用简洁的模块化设计：

```
taskhub/
├── src/                    # 源代码目录
│   ├── __init__.py
│   ├── server.py          # 主服务器入口
│   ├── tools/             # MCP工具模块
│   │   ├── __init__.py
│   │   └── taskhub.py     # Taskhub核心工具
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── task.py        # 任务模型
│   │   └── agent.py       # 代理模型
│   ├── storage/           # 数据存储层
│   │   ├── __init__.py
│   │   ├── json_store.py  # JSON文件存储
│   │   └── sqlite_store.py # SQLite归档存储
│   └── utils/             # 工具函数
│       ├── __init__.py
│       └── config.py      # 配置管理
├── tests/                 # 测试目录
│   ├── __init__.py
│   └── test_taskhub.py
├── configs/               # 配置文件
│   ├── config.yaml
│   └── logging.yaml
├── scripts/               # 脚本工具
│   ├── run_dev.sh
│   ├── run_sse.sh
│   └── run_stdio.sh
├── docs/                  # 文档目录
│   ├── ARCHITECTURE.md
│   ├── API.md
│   └── examples/
├── docker/                # Docker配置
│   ├── Dockerfile
│   └── docker-compose.yml
├── pyproject.toml         # 项目配置
├── uv.lock               # 依赖锁文件
├── .python-version       # Python版本
├── .gitignore
├── .dockerignore
└── README.md
```

#### 13.2. 核心模块设计

##### **13.2.1. 服务器入口 (src/server.py)**
基于FastMCP的统一入口，支持多种传输方式：

```python
from fastmcp import FastMCP
from src.tools.taskhub import taskhub_tools
import argparse

# 创建MCP服务器实例
mcp = FastMCP("taskhub")

# 注册工具
mcp.add_tool(taskhub_tools.task_list)
mcp.add_tool(taskhub_tools.task_claim)
mcp.add_tool(taskhub_tools.report_submit)
mcp.add_tool(taskhub_tools.task_publish)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Taskhub MCP Server')
    parser.add_argument('--transport', choices=['stdio', 'sse'], default='stdio')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--host', default='localhost')
    
    args = parser.parse_args()
    
    if args.transport == 'sse':
        mcp.run(transport='sse', host=args.host, port=args.port)
    else:
        mcp.run(transport='stdio')
```

##### **13.2.2. 工具模块 (src/tools/)**
按功能划分的工具模块，支持热插拔：

- **taskhub.py**: Taskhub核心任务管理工具

##### **13.2.3. 数据模型 (src/models/)**
Pydantic模型定义，提供类型安全和验证：

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Task(BaseModel):
    id: str = Field(..., description="任务唯一标识")
    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    capability: str = Field(..., description="所需能力")
    status: str = Field(default="pending", description="任务状态")
    assignee: Optional[str] = None
    lease_id: Optional[str] = None
    lease_expires_at: Optional[datetime] = None
    depends_on: List[str] = Field(default_factory=list)
    parent_task_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

##### **13.2.4. 存储层 (src/storage/)**
支持多种存储后端的抽象层：

- **json_store.py**: JSON文件存储（活跃任务）
- **sqlite_store.py**: SQLite归档存储（历史任务）

#### 13.3. 依赖管理

使用`pyproject.toml`进行依赖管理：

```toml
[project]
name = "taskhub"
version = "2.0.0"
description = "Taskhub MCP Server"
requires-python = ">=3.8"
dependencies = [
    "fastmcp>=0.3.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "aiosqlite>=0.19.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

#### 13.4. 容器化配置

##### **Dockerfile**
基于Python的轻量级容器：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# 安装依赖
RUN uv sync --frozen

# 暴露端口
EXPOSE 8000

# 运行命令
CMD ["uv", "run", "python", "-m", "src.server", "--transport", "sse", "--host", "0.0.0.0", "--port", "8000"]
```

##### **docker-compose.yml**
完整的开发环境配置：

```yaml
version: '3.8'

services:
  taskhub:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./configs:/app/configs
    environment:
      - PYTHONPATH=/app
    restart: unless-stopped

  taskhub-stdio:
    build: .
    volumes:
      - ./data:/app/data
      - ./configs:/app/configs
    environment:
      - PYTHONPATH=/app
    command: ["uv", "run", "python", "-m", "src.server", "--transport", "stdio"]
    stdin_open: true
    tty: true
```

#### 13.5. 开发工作流

1. **本地开发**:
   ```bash
   uv sync
   uv run python -m src.server --transport stdio
   ```

2. **SSE模式测试**:
   ```bash
   uv run python -m src.server --transport sse --port 8080
   ```

3. **容器化开发**:
   ```bash
   docker-compose up taskhub
   ```

4. **运行测试**:
   ```bash
   uv run pytest tests/
   ```

#### 13.6. 部署策略

- **独立部署**: 直接运行Python脚本
- **容器部署**: 使用Docker Compose
- **云端部署**: 支持AWS Lambda、Google Cloud Run等无服务器平台
- **边缘部署**: 支持在边缘设备上运行轻量级实例

---

### 14. 附录 A: 任务分类枚举
*   `Feature`: 实现一个新功能。
*   `Bug`: 修复代码中的一个缺陷。
*   `Research`: 进行技术调研或可行性分析。
*   `Testing`: 编写或执行测试用例。
*   `Documentation`: 编写技术文档或用户手册。
*   `Refactor`: 代码重构或架构改进。
*   `Chore`: 日常杂务，如更新依赖、配置环境等。

### 15. 附录 B: 任务优先级枚举
*   `Critical`: 阻塞性问题，必须立即处理。
*   `High`: 高优先级，应在短期内尽快完成。
*   `Medium`: 正常优先级，按计划进行（默认）。
*   `Low`: 低优先级，可在资源空闲时处理。

### 16. 附录 C: 预先定义的能力矩阵

| 能力分类 | 能力字符串 (Capability String) | 描述 | 典型代理/角色 |
| :--- | :--- | :--- | :--- |
| **项目管理** | `pm-task-create` | 创建、定义和分配新任务。 | Gemini |
| | `pm-task-prioritize` | 调整现有任务的优先级或分类。 | Gemini |
| | `pm-agent-feedback` | 对代理完成的任务提交评价和奖励。 | Gemini |
| | `pm-workflow-define` | (未来) 定义和启动复杂的多步骤工作流。 | Gemini |
| **研究与分析** | `research-library-evaluate` | 研究、评估并对比第三方库的优劣。 | KIMI |
| | `research-algorithm-design` | 设计用于数据处理或分析的核心算法。 | KIMI |
| | `research-performance-benchmark`| 对不同的实现方案进行性能基准测试。 | KIMI |
| **软件开发** | `dev-dotnet-manage` | 使用`dotnet CLI`管理解决方案和项目文件。 | Lingma |
| | `dev-csharp-implement` | 编写核心的C#业务逻辑和算法实现。 | Lingma |
| | `dev-api-integrate` | 集成第三方库或SDK的API。 | Lingma |
| | `dev-wpf-xaml` | 使用XAML构建或修改WPF用户界面布局。 | Lingma |
| | `dev-wpf-binding` | 实现WPF中的数据绑定逻辑（MVVM模式）。 | Lingma |
| | `dev-wpf-controls` | 开发或定制WPF自定义控件。 | Lingma |
| | `dev-git-commit` | 将代码变更提交到Git版本控制系统。 | Lingma |
| **数据处理** | `data-parsing-e57` | 专门负责解析和读取`.e57`点云文件格式。 | Lingma |
| | `data-parsing-las` | 专门负责解析和读取`.las`或`.laz`点云文件格式。| Lingma |
| | `data-processing-filter` | 实现对点云数据的过滤算法（如噪声过滤）。 | Lingma |
| | `data-processing-downsample` | 实现对点云数据的降采样算法。 | Lingma |
| | `data-visualization-render` | 负责将点云数据在3D视图中进行高效渲染的核心逻辑。| Lingma |
| **质量保证** | `qa-test-unit` | 编写针对特定方法或类的单元测试。 | Lingma / QA Agent |
| | `qa-test-integration` | 编写集成测试，验证多个组件协同工作的正确性。 | Lingma / QA Agent |
| | `qa-bug-reproduce` | 根据Bug报告，尝试在本地环境中稳定复现问题。 | Lingma / QA Agent |
| **文档** | `doc-technical-write` | 编写面向开发者的技术设计文档或架构说明。 | Gemini / KIMI |
| | `doc-api-reference` | 从代码注释中生成并发布API参考文档。 | Automation Agent |
| | `doc-user-guide` | 编写面向最终用户的产品使用手册。 | Gemini |
