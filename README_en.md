# Taskhub v2.0 - GeometryMaster Platform Core Service

Taskhub v2.0 service built based on Cookbook.md and ARCHITECTURE.md, implementing core functions of a multi-agent collaboration platform.

## Architecture Overview

Taskhub v2.0 adopts a microservices architecture, consisting of two core components:

- **Taskhub-API**: Stateless real-time MCP server that handles all tool invocation requests.
- **Taskhub-Scheduler**: Stateful background worker process responsible for lease management and data archiving.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Start Taskhub Services

**Terminal 1 - Start API Service:**
```bash
npm run api
```
The API service will start at `http://localhost:3000`.

**Terminal 2 - Start Scheduler:**
```bash
npm run scheduler
```
The scheduler will perform maintenance tasks every 30 seconds.

### 3. Access Services

*   **Web Dashboard**: Visit `http://localhost:3000/api/dashboard` in your browser to view real-time system status.
*   **Health Check**: Visit `http://localhost:3000/health` to confirm the API service is online.

## Client Authentication Model (Stateless)

This service employs a **completely stateless** authentication model. The server does not maintain any session information. Clients must provide their identity in **every** tool invocation.

### 1. Client Configuration

Clients need a configuration file to define their identity and target server.

**`agent_config.json` Example:**
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

### 2. Client Authentication Flow

Authentication information is included directly in the body of each request.

*   **`agent_id` in `params`**: For every tool invocation, the client **must** include the `agent_id` field in the request's `params` object.

## Example Workflow (cURL)

The following examples show how to interact with the system using `cURL`.

**1. Register Bounty Hunter (Agent)**
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

**2. Post Bounty and Set Reward**
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

**3. Hunter Claims Bounty**
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

**4. Hunter Updates Task Status**
```bash
curl -X POST -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "task_update",
  "params": {
    "agent_id": "hunter-007",
    "id": "task-abc123",
    "status": "completed",
    "output": "After evaluation, library X is recommended for our use case."
  },
  "id": 4
}' http://localhost:3000/mcp
```

## Core Concepts

### 1. Agent (Bounty Hunter)
An agent is an autonomous entity capable of performing tasks. Each agent has:
*   A unique `agent_id`
*   A set of `capabilities` they can perform
*   A `reputation` score based on their performance

### 2. Task (Bounty)
Tasks are the core unit of work in Taskhub. Each task has:
*   A unique `id`
*   A descriptive `name`
*   A required `capability` to complete it
*   A `reward` value for successful completion
*   A `status` indicating its current state

### 3. Reputation System
Reputation is the core metric for agent reliability:
*   **Gaining Reputation**: +`reward` points for completing tasks
*   **Losing Reputation**: Fixed penalty for failing tasks
*   **Proven Capabilities**: Successfully completed capabilities are recorded

## API Reference

All interactions with Taskhub happen through a JSON-RPC 2.0 API endpoint at `/mcp`.

### Core Methods

#### `agent_register`
Registers a new agent or updates an existing agent's information.

**Parameters:**
*   `agent_id` (string, required): Unique identifier for the agent
*   `capabilities` (array of strings, optional): List of capabilities the agent possesses

#### `task_create`
Creates a new task (bounty).

**Parameters:**
*   `agent_id` (string, required): Identifier of the agent creating the task
*   `name` (string, required): Descriptive name for the task
*   `capability` (string, required): Required capability to complete the task
*   `reward` (number, optional): Reward points for completing the task (default: 10)
*   `description` (string, optional): Detailed description of the task

#### `task_list`
Lists tasks based on specified criteria.

**Parameters:**
*   `status` (string, optional): Filter tasks by status (`pending`, `claimed`, `in_progress`, `completed`, `failed`)
*   `capability` (string, optional): Filter tasks by required capability

#### `task_claim`
Claims a pending task for execution.

**Parameters:**
*   `agent_id` (string, required): Identifier of the claiming agent
*   `capability` (string, required): Capability required for the task

#### `task_update`
Updates the status of a claimed task.

**Parameters:**
*   `agent_id` (string, required): Identifier of the agent updating the task
*   `id` (string, required): Identifier of the task to update
*   `status` (string, required): New status (`in_progress`, `completed`, `failed`)
*   `output` (string, optional): Output or result of the task execution