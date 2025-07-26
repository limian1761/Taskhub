// 封装了所有与数据库的交互。
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import Database from 'better-sqlite3';

// 初始化活跃数据库 (LowDB)
const activeAdapter = new JSONFile('data/taskhub_active.json');
const activeDb = new Low(activeAdapter, { tasks: [], agents: [] });
await activeDb.read();

// 初始化归档数据库 (SQLite)
const archiveDb = new Database('data/taskhub_archive.db', { verbose: console.log });

// 创建归档任务表 (如果不存在)
archiveDb.exec(`
  CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    parent_task_id TEXT,
    depends_on TEXT,
    name TEXT,
    details TEXT,
    capability TEXT,
    category TEXT,
    priority TEXT,
    status TEXT,
    assignee TEXT,
    lease_id TEXT,
    lease_expires_at TEXT,
    output TEXT,
    created_at TEXT,
    updated_at TEXT,
    history TEXT
  )
`);

export { activeDb, archiveDb };
