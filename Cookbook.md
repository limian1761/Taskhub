Cookbook好的，遵照您的指示。这是一份专门为另一个AI（或开发者）构建`Taskhub v2.0`而设计的“烹饪手册”（Cookbook）。它包含了所有必要的参考文件清单和一系列清晰、循序渐进的命令提示词。

---

### AI Cookbook: 构建 Taskhub v2.0

**目标:** 本手册旨在指导一个AI或人类开发者，根据`Taskhub 设计文档 v2.0`，从零开始完整地构建并运行`Taskhub`服务。

**核心技术栈:**
*   **运行时:** Node.js (建议 v18 或更高版本)
*   **包管理器:** npm
*   **框架与库:** Express.js, lowdb, async-mutex, uuid

---

### 1. 参考文件清单 (The Ingredients)

以下是构建`Taskhub v2.0`所需的全部源文件。请将它们创建在指定的目录结构中。

#### **项目根目录 (`taskhub/`)**

**`taskhub/package.json`**
```json
{
  "name": "taskhub-v2.0",
  "version": "2.0.0",
  "description": "The central MCP server for the GeometryMaster platform.",
  "main": "api_server.js",
  "type": "module",
  "scripts": {
    "api": "node src/api_server.js",
    "scheduler": "node src/scheduler.js",
    "dev:api": "nodemon src/api_server.js"
  },
  "dependencies": {
    "async-mutex": "^0.5.0",
    "express": "^4.19.2",
    "lowdb": "^7.0.1",
    "uuid": "^9.0.1"
  },
  "devDependencies": {
    "nodemon": "^3.1.0"
  }
}
```

#### **数据层 (`taskhub/src/`)**

**`taskhub/src/database.js`**
```javascript
// 封装了所有与 lowdb 的交互，实现了活跃数据库与归档数据库的分离。
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';

// 初始化活跃数据库
const activeAdapter = new JSONFile('data/taskhub_active.json');
const activeDb = new Low(activeAdapter, { tasks: [], agents: [] });
await activeDb.read();

// 初始化归档数据库 (使用JSON作为示例，SQLite更佳)
const archiveAdapter = new JSONFile('data/taskhub_archive.json');
const archiveDb = new Low(archiveAdapter, { tasks: [] });
await archiveDb.read();

export { activeDb, archiveDb };
```

#### **核心逻辑 (`taskhub/src/`)**

**`taskhub/src/tools.js`**
```javascript
// 包含了所有MCP工具的核心业务逻辑实现。
import { activeDb } from './database.js';
import { v4 as uuidv4 } from 'uuid';

// Helper to check if a task's dependencies are met
async function areDependenciesMet(task) {
    if (!task.depends_on || task.depends_on.length === 0) {
        return true;
    }
    const dependentTasks = activeDb.data.tasks.filter(t => task.depends_on.includes(t.id));
    return dependentTasks.every(t => t.status === 'completed');
}

// ---- Task Management Tools ----

export async function task_create(args) {
    const { name, capability, parent_task_id = null, depends_on = [], ...rest } = args;
    if (!name || !capability) throw new Error("Missing required arguments: name, capability");

    const newTask = {
        id: `task-${uuidv4().slice(0, 8)}`,
        name,
        capability,
        parent_task_id,
        depends_on,
        category: 'Feature',
        priority: 'Medium',
        status: 'pending',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        history: [{ status: 'pending', timestamp: new Date().toISOString() }],
        ...rest
    };
    activeDb.data.tasks.push(newTask);
    await activeDb.write();
    return newTask;
}

export async function task_list(filter = {}) {
    if (Object.keys(filter).length === 0) return activeDb.data.tasks;
    return activeDb.data.tasks.filter(task => {
        return Object.keys(filter).every(key => task[key] === filter[key]);
    });
}

export async function task_claim(args) {
    const { capability, agent_id, lease_duration_seconds = 600 } = args;
    // 按优先级排序查找可认领任务
    const claimableTasks = activeDb.data.tasks
        .filter(t => t.status === 'pending' && t.capability === capability)
        .sort((a, b) => { // A simplified priority sort
            const priorities = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
            return (priorities[b.priority] || 0) - (priorities[a.priority] || 0);
        });

    for (const task of claimableTasks) {
        if (await areDependenciesMet(task)) {
            task.status = 'claimed';
            task.assignee = agent_id;
            task.lease_id = `lease-${uuidv4()}`;
            task.lease_expires_at = new Date(Date.now() + lease_duration_seconds * 1000).toISOString();
            task.updated_at = new Date().toISOString();
            task.history.push({ status: 'claimed', assignee: agent_id, timestamp: task.updated_at });
            await activeDb.write();
            return task;
        }
    }
    return null; // No claimable task found
}

export async function task_update(args) {
    const { id, lease_id, ...updates } = args;
    const task = activeDb.data.tasks.find(t => t.id === id);
    if (!task) throw new Error(`Task with id ${id} not found.`);

    // Security: If task is claimed, a valid lease_id must be provided for most updates
    if (task.status === 'claimed' && task.lease_id && task.lease_id !== lease_id) {
        if (!updates.status || (updates.status !== 'pending' && updates.status !== 'failed'))
        throw new Error("Invalid or missing lease_id to update a claimed task.");
    }
    
    // Completion Gate: Prevent parent task completion if subtasks are not done
    if (updates.status === 'completed') {
        const subtasks = activeDb.data.tasks.filter(t => t.parent_task_id === id);
        if (subtasks.some(st => st.status !== 'completed' && st.status !== 'cancelled')) {
            throw new Error(`Cannot complete task ${id}: one or more subtasks are not finished.`);
        }
    }

    Object.assign(task, updates);
    task.updated_at = new Date().toISOString();
    if (updates.status) {
      task.history.push({ status: updates.status, timestamp: task.updated_at });
    }
    await activeDb.write();
    return task;
}

// ---- Agent Management (Simplified) ----
export async function agent_register(args) {
    const { agent_id, capabilities } = args;
    let agent = activeDb.data.agents.find(a => a.id === agent_id);
    if (agent) {
        agent.last_seen_at = new Date().toISOString();
        agent.capabilities = capabilities;
    } else {
        agent = { id: agent_id, capabilities, last_seen_at: new Date().toISOString(), status: 'active', performance_metrics: {} };
        activeDb.data.agents.push(agent);
    }
    await activeDb.write();
    return agent;
}
```

#### **服务入口 (`taskhub/src/`)**

**`taskhub/src/api_server.js`**
```javascript
// Taskhub-API 微服务的主入口，负责处理实时的 MCP 请求。
import express from 'express';
import { Mutex } from 'async-mutex';
import * as tools from './tools.js';

const app = express();
app.use(express.json());
const PORT = process.env.PORT || 3000;

const writeLock = new Mutex();
const WRITE_OPERATIONS = new Set(['task_create', 'task_claim', 'task_update', 'agent_register']);

// MCP Endpoint
app.post('/', async (req, res) => {
    const { jsonrpc, method, params, id } = req.body;

    if (jsonrpc !== '2.0' || !method || !id) {
        return res.status(400).json({ id, jsonrpc, error: { code: -32600, message: 'Invalid Request' }});
    }

    if (typeof tools[method] !== 'function') {
        return res.json({ id, jsonrpc, error: { code: -32601, message: 'Method not found' }});
    }

    const execute = async () => {
        try {
            const result = await tools[method](params);
            res.json({ id, jsonrpc, result });
        } catch (error) {
            res.json({ id, jsonrpc, error: { code: -32000, message: error.message }});
        }
    };

    if (WRITE_OPERATIONS.has(method)) {
        const release = await writeLock.acquire();
        try {
            await execute();
        } finally {
            release();
        }
    } else { // Read operation
        await execute();
    }
});

app.listen(PORT, () => {
    console.log(`Taskhub-API server listening on port ${PORT}`);
});
```

**`taskhub/src/scheduler.js`**
```javascript
// Taskhub-Scheduler 微服务的主入口，负责处理后台的、时间驱动的任务。
import * as tools from './tools.js';

const LEASE_CHECK_INTERVAL = 60 * 1000; // 1 minute
const ARCHIVE_INTERVAL = 60 * 60 * 1000; // 1 hour
const ARCHIVE_AGE_DAYS = 30;

async function releaseExpiredLeases() {
    console.log('[Scheduler] Checking for expired leases...');
    const claimedTasks = await tools.task_list({ status: 'claimed' });
    const now = new Date();

    for (const task of claimedTasks) {
        if (task.lease_expires_at && new Date(task.lease_expires_at) < now) {
            console.log(`[Scheduler] Lease for task ${task.id} has expired. Releasing.`);
            try {
                await tools.task_update({
                    id: task.id,
                    lease_id: task.lease_id, // Provide lease_id to bypass security check for this specific reset
                    status: 'pending',
                    assignee: null,
                    lease_id: null,
                    lease_expires_at: null
                });
            } catch (error) {
                console.error(`[Scheduler] Error releasing task ${task.id}:`, error.message);
            }
        }
    }
}

async function archiveOldTasks() {
    // This is a simplified placeholder. A real implementation would move
    // tasks from activeDb to archiveDb.
    console.log(`[Scheduler] Archiving tasks older than ${ARCHIVE_AGE_DAYS} days is not yet implemented.`);
}

console.log('Taskhub-Scheduler started.');
setInterval(releaseExpiredLeases, LEASE_CHECK_INTERVAL);
// setInterval(archiveOldTasks, ARCHIVE_INTERVAL);
```

---

### 2. 命令提示词 (The Cookbook Steps)

请按顺序向构建AI或开发者提供以下提示词。

**提示词 1: "项目初始化"**
> “请创建一个名为`taskhub`的目录。在其中创建`data`和`src`两个子目录。然后，在`taskhub`根目录下创建`package.json`文件，内容使用参考文件清单中提供的内容。最后，在`taskhub`目录下运行`npm install`来安装所有依赖。”

**提示词 2: "构建数据访问层"**
> “在`taskhub/src`目录下，创建`database.js`文件。这个文件将负责初始化活跃数据库和归档数据库。请使用参考文件清单中提供的代码。”

**提示词 3: "实现核心工具逻辑"**
> “在`taskhub/src`目录下，创建`tools.js`文件。这是系统的核心，包含了所有任务和代理管理的业务逻辑，包括任务的创建、认领和更新。请完整复制参考文件清单中的代码，并仔细阅读其中的注释以理解其工作原理。”

**提示词 4: "构建 Taskhub-API 微服务"**
> “在`taskhub/src`目录下，创建`api_server.js`文件。这是面向客户端的实时MCP服务器，它将处理所有传入的工具调用请求，并使用互斥锁来保证写操作的原子性。请使用参考清单中的代码。”

**提示词 5: "构建 Taskhub-Scheduler 微服务"**
> “在`taskhub/src`目录下，创建`scheduler.js`文件。这是后台工作进程，负责执行如释放过期租约之类的定时维护任务。请使用参考清单中的代码。”

**提示词 6: "运行与验证"**
> “现在所有文件都已创建完毕。你需要打开两个独立的终端，都切换到`taskhub`根目录。
> *   在**第一个终端**中，运行命令 `npm run api` 来启动API服务。
> *   在**第二个终端**中，运行命令 `npm run scheduler` 来启动调度器服务。
>
> 两个服务都成功启动后，`Taskhub v2.0`平台就已完全构建并投入运行。你可以开始通过向`http://localhost:3000`发送MCP请求来与它交互了。”