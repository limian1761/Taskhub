// Taskhub-Scheduler 后台工作进程
import { activeDb, archiveDb } from './database.js';
import * as tools from './tools.js';

const SCHEDULE_INTERVAL = 30000; // 30 seconds
const LEASE_TIMEOUT = 600; // 10 minutes in seconds

console.log('Taskhub-Scheduler started...');

async function releaseExpiredLeases() {
    try {
        const tasks = await tools.task_list({ status: 'claimed' });
        const now = new Date();
        
        for (const task of tasks) {
            if (task.lease_expires_at && new Date(task.lease_expires_at) < now) {
                console.log(`[Scheduler] Releasing expired lease for task ${task.id}`);
                // 使用内部调用，避免触发不必要的检查
                const taskToUpdate = activeDb.data.tasks.find(t => t.id === task.id);
                if (taskToUpdate) {
                    taskToUpdate.status = 'pending';
                    taskToUpdate.assignee = null;
                    taskToUpdate.lease_id = null;
                    taskToUpdate.lease_expires_at = null;
                    taskToUpdate.history.push({ status: 'lease_expired', timestamp: new Date().toISOString() });
                }
            }
        }
        await activeDb.write();
    } catch (error) {
        console.error('[Scheduler] Error releasing expired leases:', error);
    }
}

async function archiveOldTasks() {
    console.log('[Scheduler] Checking for tasks to archive...');
    try {
        const tasksToArchive = activeDb.data.tasks.filter(t => 
            t.status === 'completed' || t.status === 'cancelled'
        );
        
        if (tasksToArchive.length === 0) {
            console.log('[Scheduler] No tasks to archive.');
            return;
        }

        console.log(`[Scheduler] Found ${tasksToArchive.length} tasks to archive.`);

        const insertStmt = archiveDb.prepare(`
            INSERT INTO tasks (
                id, parent_task_id, depends_on, name, details, capability, 
                category, priority, status, assignee, lease_id, lease_expires_at, 
                output, created_at, updated_at, history
            ) VALUES (
                @id, @parent_task_id, @depends_on, @name, @details, @capability,
                @category, @priority, @status, @assignee, @lease_id, @lease_expires_at,
                @output, @created_at, @updated_at, @history
            )
        `);

        const archiveTransaction = archiveDb.transaction((tasks) => {
            for (const task of tasks) {
                const taskForSqlite = { ...task };
                // SQLite doesn't have a native array type, so we serialize to JSON strings
                taskForSqlite.depends_on = JSON.stringify(task.depends_on || []);
                taskForSqlite.history = JSON.stringify(task.history || []);
                // Ensure all fields exist to avoid binding errors
                taskForSqlite.parent_task_id = task.parent_task_id || null;
                taskForSqlite.details = task.details || null;
                taskForSqlite.assignee = task.assignee || null;
                taskForSqlite.lease_id = task.lease_id || null;
                taskForSqlite.lease_expires_at = task.lease_expires_at || null;
                taskForSqlite.output = task.output ? JSON.stringify(task.output) : null;

                insertStmt.run(taskForSqlite);
            }
        });

        archiveTransaction(tasksToArchive);
        console.log(`[Scheduler] Successfully inserted ${tasksToArchive.length} tasks into archive DB.`);

        // Remove archived tasks from the active database
        const archivedIds = new Set(tasksToArchive.map(t => t.id));
        activeDb.data.tasks = activeDb.data.tasks.filter(t => !archivedIds.has(t.id));
        await activeDb.write();
        
        console.log(`[Scheduler] Successfully removed archived tasks from active DB.`);

    } catch (error) {
        console.error('[Scheduler] Error archiving tasks:', error);
    }
}

async function runScheduler() {
    console.log(`\n[Scheduler] Running cycle at ${new Date().toISOString()}`);
    await releaseExpiredLeases();
    await archiveOldTasks();
}

// Run immediately on startup
runScheduler();

// Schedule periodic runs
setInterval(runScheduler, SCHEDULE_INTERVAL);

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n[Scheduler] Shutting down...');
    archiveDb.close(); // Close the database connection
    console.log('[Scheduler] Archive DB connection closed.');
    process.exit(0);
});