# GeometryMaster 平台 - Taskhub 服务详细设计文档

**版本:** 2.0
**日期:** 2025年7月26日
**变更摘要:** 引入v2.0架构，包括服务解耦、任务依赖(DAG)、数据归档和代理子任务创建能力，旨在实现平台的长期可扩展性、高级自动化与智能。

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
13. [附录 A: 任务分类枚举](#13-附录-a-任务分类枚举)
14. [附录 B: 任务优先级枚举](#14-附录-b-任务优先级枚举)
15. [附录 C: 预先定义的能力矩阵](#15-附录-c-预先定义的能力矩阵)

---

### 1. 引言
本文档定义了`Taskhub`服务 v2.0 的技术架构与设计。此版本在前一版的基础上进行了重大升级，旨在解决长期运行的扩展性问题，并引入了高级自动化与智能机制，为`GeometryMaster`平台构建一个更健壮、更智能的未来。

### 2. 设计哲学与核心原则
v2.0 继承并强化了原有的核心原则：
*   **协议驱动 (Protocol-Driven)**
*   **状态原子性 (State Atomicity)**
*   **逻辑与传输解耦 (Logic/Transport Decoupling)**
*   **(新增) 服务解耦与可扩展性 (Service Decoupling & Scalability)**

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
     | (MCP Tool Calls, e.g., task_list, task_update)
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
(无变化)

### 5. MCP 工具集 API 详述 (v2.0)

*   **`task_create(args)`**:
    *   **args** 新增: `{ parent_task_id, depends_on }`。
*   **`task_claim(args)`**:
    *   **核心逻辑变更**: 现在只会返回那些`status`为`pending`**且**所有`depends_on`任务都已`completed`的任务。
*   **`task_update(args)`**:
    *   **核心逻辑变更**: 增加“完成门控”。当尝试将一个任务状态更新为`completed`时，系统会检查该任务是否拥有子任务（通过`parent_task_id`反查）。如果有任何子任务未完成，此操作将被拒绝。

### 6. 客户端集成策略
(无变化)

### 7. 核心机制：并发控制与任务租约
(机制本身无变化，但由`Taskhub-Scheduler`负责租约的超时释放)

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
*   **解决方案**: 允许代理通过调用`task_create`来创建子任务。
    *   **分而治之**: 代理在执行一个复杂任务时（如`实现点云处理模块`），可以将其分解为更小的、可管理的子任务（如`子任务1: 解析E57`，`子任务2: 实现滤波算法`），并为这些子任务设置正确的`capability`。
    *   **涌现式协作**: 一个代理创建的子任务可以被其他更专业的代理认领，从而实现代理间的动态、自主协作。
    *   **完成门控**: 父任务的完成状态与其所有子任务的完成状态绑定，确保了工作的完整性。

### 11. 核心工作流示例 (v2.0)
一个包含依赖和子任务的复杂功能开发流程：
1.  **定义工作流 (Host)**: `Gemini`一次性创建三个任务：
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

### 13. 附录 A: 任务分类枚举
*   `Feature`: 实现一个新功能。
*   `Bug`: 修复代码中的一个缺陷。
*   `Research`: 进行技术调研或可行性分析。
*   `Testing`: 编写或执行测试用例。
*   `Documentation`: 编写技术文档或用户手册。
*   `Refactor`: 代码重构或架构改进。
*   `Chore`: 日常杂务，如更新依赖、配置环境等。

### 14. 附录 B: 任务优先级枚举
*   `Critical`: 阻塞性问题，必须立即处理。
*   `High`: 高优先级，应在短期内尽快完成。
*   `Medium`: 正常优先级，按计划进行（默认）。
*   `Low`: 低优先级，可在资源空闲时处理。

### 15. 附录 C: 预先定义的能力矩阵

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
