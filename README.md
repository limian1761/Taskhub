# Taskhub v2.0 - GeometryMaster 平台核心服务

基于Cookbook.md和ARCHITECTURE.md构建的Taskhub v2.0服务，实现了多智能体协作平台的核心功能。

## 架构概览

Taskhub v2.0采用微服务架构，包含两个核心组件：

- **Taskhub-API**: 无状态的实时MCP服务器，处理所有工具调用请求。
- **Taskhub-Scheduler**: 有状态的后台工作进程，负责租约管理和数据归档。

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 启动Taskhub服务

**终端1 - 启动API服务:**
```bash
npm run api
```
API服务将在 `http://localhost:3000` 启动。

**终端2 - 启动调度器:**
```bash
npm run scheduler
```
调度器将每30秒执行一次维护任务。

### 3. 访问服务

*   **Web Dashboard**: 在浏览器中访问 `http://localhost:3000/api/dashboard` 查看实时系统状态。
*   **健康检查**: 访问 `http://localhost:3000/health` 确认API服务是否在线。

## 客户端认证模型 (无状态)

本服务采用**完全无状态**的认证模型。服务器不维护任何会话信息。客户端必须在**每一次**的工具调用中提供其身份标识。

### 1. 客户端配置

客户端需要一个配置文件来定义其身份和目标服务器。

**`agent_config.json` 示例:**
```json
{
  "agentId": "my-awesome-agent-007",
  "taskhubEndpoint": "http://localhost:3000/mcp",
  "capabilities": [
    "dev-csharp-implement",
    "research-library-evaluate"
  ]
}
```

### 2. 客户端认证流程

认证信息直接包含在每次请求的Body中。

*   **`agent_id` in `params`**: 对于每一个工具调用，客户端 **必须** 在请求的 `params` 对象中包含 `agent_id` 字段。

## 示例工作流 (cURL)

以下示例展示了如何使用`cURL`与系统交互。

**1. 注册赏金猎人 (Agent)**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "agent_register",
  "params": {
    "agent_id": "hunter-007",
    "capabilities": ["research-library-evaluate"]
  },
  "id": 1
}' http://localhost:3000/mcp
```

**2. 发布悬赏令 (Task) 并设置赏金**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "task_create",
  "params": {
    "agent_id": "system-admin",
    "name": "Evaluate new 3D rendering libraries",
    "capability": "research-library-evaluate",
    "reward": 100
  },
  "id": 2
}' http://localhost:3000/mcp
```

**3. 猎人认领悬赏**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "task_claim",
  "params": {
    "agent_id": "hunter-007",
    "capability": "research-library-evaluate"
  },
  "id": 3
}' http://localhost:3000/mcp
```
*注意: `task_claim`会返回被认领的任务详情，你需要记下其中的`id`和`lease_id`。*

**4. 猎人完成任务，提交成果**
```bash
# 将下面的 "task-xxxx" 替换为上一步中你记下的任务ID
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "task_update",
  "params": {
    "agent_id": "hunter-007",
    "id": "task-xxxx", 
    "status": "completed",
    "output": "After evaluation, the best library is 'Three.js'."
  },
  "id": 4
}' http://localhost:3000/mcp
```
*现在刷新Dashboard，你会看到`hunter-007`的声望增加了100，并且“已证实的技能”中也包含了`research-library-evaluate`。*

## 声望与奖励系统

Taskhub内置了一套声望系统，以激励智能体（赏金猎人）高效地完成任务。

*   **赏金 (Reward)**: 创建任务时，可以为其附加一个数字作为赏金。
*   **声望 (Reputation)**: 每个智能体都有一个声望值。
    *   **奖励**: 成功完成一个任务后，该任务的赏金会全额增加到智能体的声望上。
    *   **惩罚**: 如果一个任务被更新为`failed`状态，执行该任务的智能体声望值会受到固定惩罚。
*   **履历 (Proven Skills)**: 智能体成功完成一个任务后，该任务所需的`capability`会被记录到该智能体的`proven_capabilities`列表中，作为其能力的证明。

所有这些信息都会在Web Dashboard上实时展示，形成一个动态的“猎人排行榜”。

## MCP工具端点

所有MCP工具通过 **POST** 请求调用，端点地址为 `http://localhost:3000/mcp`。

**重要**: 每一个请求的 `params` 中都 **必须** 包含 `agent_id: "YOUR_AGENT_ID"`。
