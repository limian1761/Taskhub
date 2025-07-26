// Taskhub-API - Refactored with @modelcontextprotocol/sdk
import express from 'express';
import cors from 'cors';
import { randomUUID } from 'node:crypto';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import * as tools from './tools.js';
import { archiveDb } from './database.js';

const PORT = process.env.PORT || 3000;

// 1. Create the Express App and basic middleware
const app = express();
app.use(express.json());

// 2. Configure CORS according to the MCP guide
app.use(cors({
  origin: '*', // Adjust for production
  exposedHeaders: ['Mcp-Session-Id'],
  allowedHeaders: ['Content-Type', 'mcp-session-id'],
}));

// 3. Set up the MCP Server
function createMcpServer() {
    const server = new McpServer({
        name: "taskhub-mcp-server",
        version: "2.0.0"
    });

    // Register all tools from tools.js using the modern `registerTool` method
    server.registerTool("task_create", {
        title: "Create Task",
        description: "Create a new task in the task hub.",
        inputSchema: {
            name: z.string().describe("The name of the task."),
            capability: z.string().describe("The capability required to perform the task."),
            parent_task_id: z.string().optional().describe("The ID of the parent task, if any."),
            depends_on: z.array(z.string()).optional().describe("A list of task IDs that this task depends on.")
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.task_create(params)) }] }));

    server.registerTool("task_list", {
        title: "List Tasks",
        description: "List tasks, optionally filtering by properties.",
        inputSchema: {
            status: z.string().optional().describe("Filter tasks by status (e.g., pending, claimed, completed)."),
            capability: z.string().optional().describe("Filter tasks by required capability.")
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.task_list(params)) }] }));

    server.registerTool("task_get", {
        title: "Get Task",
        description: "Get the details of a specific task by its ID.",
        inputSchema: {
            id: z.string().describe("The ID of the task to retrieve.")
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.task_get(params)) }] }));

    server.registerTool("task_claim", {
        title: "Claim Task",
        description: "Claim an available task that matches a given capability.",
        inputSchema: {
            capability: z.string().describe("The capability to match for claiming a task."),
            agent_id: z.string().describe("The ID of the agent claiming the task."),
            lease_duration_seconds: z.number().optional().describe("The duration in seconds for which the task is leased.")
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.task_claim(params)) }] }));

    server.registerTool("task_update", {
        title: "Update Task",
        description: "Update a task's properties, such as its status or details.",
        inputSchema: {
            id: z.string().describe("The ID of the task to update."),
            lease_id: z.string().optional().describe("The lease ID, required if the task is claimed."),
            status: z.string().optional().describe("The new status of the task.")
            // Note: other properties can be passed as well, zod can be configured to allow this.
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.task_update(params)) }] }));

    server.registerTool("agent_list", {
        title: "List Agents",
        description: "List all registered agents.",
        inputSchema: {}
    }, async () => ({ content: [{ type: 'text', text: JSON.stringify(await tools.agent_list()) }] }));

    server.registerTool("agent_register", {
        title: "Register Agent",
        description: "Register a new agent or update an existing one.",
        inputSchema: {
            agent_id: z.string().describe("The unique ID of the agent."),
            capabilities: z.array(z.string()).describe("The capabilities of the agent.")
        }
    }, async (params) => ({ content: [{ type: 'text', text: JSON.stringify(await tools.agent_register(params)) }] }));
    
    return server;
}

// 3. Set up the MCP Server
const server = createMcpServer();

// 4. Stateless MCP Request Handler
app.all('/mcp', async (req, res) => {
    const requestBody = req.body;

    // Basic validation
    if (!requestBody || typeof requestBody.method !== 'string') {
        return res.status(400).json({
            jsonrpc: '2.0',
            error: { code: -32600, message: 'Invalid Request' },
            id: requestBody?.id || null,
        });
    }

    try {
        // In this model, we create a new server instance for each request.
        // This is a simplified approach for a stateless server.
        const server = createMcpServer();
        
        // We use a temporary, in-memory transport for a single request-response cycle.
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: () => randomUUID(), // Session is ephemeral, for one request only
        });

        // The server must be connected to a transport to process the request.
        await server.connect(transport);
        
        // Handle the request and wait for the response.
        await transport.handleRequest(req, res, requestBody);

    } catch (error) {
        console.error("Error processing MCP request:", error);
        res.status(500).json({
            jsonrpc: '2.0',
            error: { code: -32000, message: 'Internal Server Error' },
            id: requestBody?.id || null,
        });
    }
});


// 5. Health check and other non-MCP routes
app.get('/health', (req, res) => {
    res.json({ status: 'ok', service: 'Taskhub-API' });
});

app.get('/api/dashboard', async (req, res) => {
    try {
        const tasks = await tools.task_list();
        const agents = (await tools.agent_list()).sort((a, b) => b.reputation - a.reputation);
        
        let archivedTasks = [];
        let archivedTaskCount = 0;
        try {
            const countRow = archiveDb.prepare('SELECT COUNT(*) as count FROM tasks').get();
            archivedTaskCount = countRow.count;
            // Fetch the last 20 archived tasks
            archivedTasks = archiveDb.prepare('SELECT * FROM tasks ORDER BY updated_at DESC LIMIT 20').all();
        } catch (dbError) {
            console.error("Could not query archive database:", dbError);
        }

        const statusColors = {
            pending: '#f0ad4e',
            claimed: '#0275d8',
            completed: '#5cb85c',
            cancelled: '#6c757d',
            failed: '#d9534f'
        };

        const html = `
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Taskhub Dashboard</title>
                <meta http-equiv="refresh" content="15">
                <link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.min.css">
                <style>
                    body { padding: 2rem; }
                    .status-badge { display: inline-block; padding: 0.25em 0.6em; font-size: 75%; font-weight: 700; line-height: 1; text-align: center; white-space: nowrap; vertical-align: baseline; border-radius: 0.25rem; color: #fff; }
                    .reputation { font-weight: bold; }
                    .rep-positive { color: #38a169; }
                    .rep-negative { color: #e53e3e; }
                    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
                    details { background-color: #f7f7f7; border-radius: 0.5rem; padding: 1rem; margin-top: 2rem; }
                </style>
            </head>
            <body>
                <main class="container">
                    <header>
                        <h1>Taskhub Dashboard</h1>
                        <p>A live view of the Bounty Board and the Hunter's Guild. Page auto-refreshes every 15 seconds.</p>
                    </header>

                    <section>
                        <h2>Guild Summary</h2>
                        <div class="summary-grid">
                            <article><h4>Active Bounties</h4><h2>${tasks.length}</h2></article>
                            <article><h4>Archived Bounties</h4><h2>${archivedTaskCount}</h2></article>
                            <article><h4>Registered Hunters</h4><h2>${agents.length}</h2></article>
                        </div>
                    </section>

                    <section>
                        <h2>Bounty Board (Active Tasks)</h2>
                        <figure>
                        <table role="grid">
                            <thead><tr><th>ID</th><th>Bounty (Name)</th><th>Reward</th><th>Status</th><th>Capability</th><th>Hunter (Assignee)</th></tr></thead>
                            <tbody>
                                ${tasks.map(task => `
                                    <tr>
                                        <td><small>${task.id}</small></td>
                                        <td>${task.name}</td>
                                        <td><strong class="rep-positive">${task.reward || 0}</strong></td>
                                        <td><span class="status-badge" style="background-color: ${statusColors[task.status] || '#6c757d'}">${task.status}</span></td>
                                        <td><code>${task.capability}</code></td>
                                        <td>${task.assignee || 'N/A'}</td>
                                    </tr>
                                `).join('') || '<tr><td colspan="6">No active bounties.</td></tr>'}
                            </tbody>
                        </table>
                        </figure>
                    </section>

                    <section>
                        <h2>Hunter's Guild (Registered Agents)</h2>
                        <figure>
                        <table role="grid">
                            <thead><tr><th>Rank</th><th>Hunter ID</th><th>Reputation</th><th>Completed</th><th>Failed</th><th>Declared Skills</th><th>Proven Skills</th></tr></thead>
                            <tbody>
                                ${agents.map((agent, index) => `
                                    <tr>
                                        <td>${index + 1}</td>
                                        <td><strong>${agent.id}</strong></td>
                                        <td><span class="reputation ${agent.reputation >= 0 ? 'rep-positive' : 'rep-negative'}">${agent.reputation}</span></td>
                                        <td>${agent.completed_tasks}</td>
                                        <td>${agent.failed_tasks}</td>
                                        <td>${agent.capabilities.map(c => `<code>${c}</code>`).join(' ')}</td>
                                        <td>${agent.proven_capabilities.map(c => `<code style="border-color: #38a169;">${c}</code>`).join(' ')}</td>
                                    </tr>
                                `).join('') || '<tr><td colspan="7">No hunters have registered.</td></tr>'}
                            </tbody>
                        </table>
                        </figure>
                    </section>

                    <details>
                        <summary>View The Archives (Last 20)</summary>
                        <figure>
                        <table role="grid">
                            <thead><tr><th>ID</th><th>Name</th><th>Final Status</th><th>Assignee</th><th>Updated At</th></tr></thead>
                            <tbody>
                                ${archivedTasks.map(task => `
                                    <tr>
                                        <td><small>${task.id}</small></td>
                                        <td>${task.name}</td>
                                        <td><span class="status-badge" style="background-color: ${statusColors[task.status] || '#6c757d'}">${task.status}</span></td>
                                        <td>${task.assignee || 'N/A'}</td>
                                        <td><small>${new Date(task.updated_at).toLocaleString()}</small></td>
                                    </tr>
                                `).join('') || '<tr><td colspan="5">The archives are empty.</td></tr>'}
                            </tbody>
                        </table>
                        </figure>
                    </details>
                </main>
            </body>
            </html>
        `;
        res.send(html);
    } catch (error) {
        res.status(500).send(`<h1>Error</h1><p>${error.message}</p>`);
    }
});


// 6. Start the server
app.listen(PORT, () => {
    console.log(`Taskhub-API MCP Server running on http://localhost:${PORT}/mcp`);
    console.log(`Dashboard available at http://localhost:${PORT}/api/dashboard`);
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\nShutting down Taskhub-API...');
    process.exit(0);
});