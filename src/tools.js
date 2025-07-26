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
    const { name, capability, parent_task_id = null, depends_on = [], reward = 0, ...rest } = args;
    if (!name || !capability) throw new Error("Missing required arguments: name, capability");

    const newTask = {
        id: `task-${uuidv4().slice(0, 8)}`,
        name,
        capability,
        parent_task_id,
        depends_on,
        reward, // Added reward field
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

export async function task_get(args) {
    const { id } = args;
    if (!id) throw new Error("Missing required argument: id");
    
    const task = activeDb.data.tasks.find(t => t.id === id);
    if (!task) throw new Error(`Task with id ${id} not found.`);
    
    return task;
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
    const { id, agent_id, ...updates } = args;
    if (!id) throw new Error("Missing required argument: id");

    const task = activeDb.data.tasks.find(t => t.id === id);
    if (!task) throw new Error(`Task with id ${id} not found.`);

    // Security: If task is claimed, a valid agent_id must be provided
    if (task.status === 'claimed' && task.assignee !== agent_id) {
        throw new Error(`Agent ${agent_id} cannot update a task assigned to ${task.assignee}.`);
    }
    
    // Completion Gate
    if (updates.status === 'completed') {
        const subtasks = activeDb.data.tasks.filter(t => t.parent_task_id === id);
        if (subtasks.some(st => st.status !== 'completed' && st.status !== 'cancelled')) {
            throw new Error(`Cannot complete task ${id}: one or more subtasks are not finished.`);
        }
    }

    // --- Reputation & Statistics Logic ---
    const agent = activeDb.data.agents.find(a => a.id === task.assignee);
    if (agent && updates.status && updates.status !== task.status) {
        const REPUTATION_PENALTY = 10; // Penalty for failing a task

        if (updates.status === 'completed') {
            agent.reputation += (task.reward || 0);
            agent.completed_tasks += 1;
            if (!agent.proven_capabilities.includes(task.capability)) {
                agent.proven_capabilities.push(task.capability);
            }
            console.log(`Agent ${agent.id} completed task ${task.id}. Reputation +${task.reward || 0}.`);
        } else if (updates.status === 'failed') {
            agent.reputation -= REPUTATION_PENALTY;
            agent.failed_tasks += 1;
            console.log(`Agent ${agent.id} failed task ${task.id}. Reputation -${REPUTATION_PENALTY}.`);
        }
    }
    // --- End of Reputation Logic ---

    Object.assign(task, updates);
    task.updated_at = new Date().toISOString();
    if (updates.status) {
      task.history.push({ status: updates.status, timestamp: task.updated_at });
    }
    await activeDb.write();
    return task;
}

// ---- Agent Management (Simplified) ----
export async function agent_list() {
    return activeDb.data.agents;
}

export async function agent_register(args) {
    const { agent_id, capabilities } = args;
    if (!agent_id) throw new Error("Missing required argument: agent_id");

    let agent = activeDb.data.agents.find(a => a.id === agent_id);
    if (agent) {
        agent.last_seen_at = new Date().toISOString();
        // Allow agents to update their declared capabilities
        agent.capabilities = capabilities || agent.capabilities;
    } else {
        agent = { 
            id: agent_id, 
            capabilities: capabilities || [], 
            last_seen_at: new Date().toISOString(), 
            status: 'active',
            // Initialize reputation system fields
            reputation: 0,
            completed_tasks: 0,
            failed_tasks: 0,
            proven_capabilities: []
        };
        activeDb.data.agents.push(agent);
    }
    await activeDb.write();
    return agent;
}