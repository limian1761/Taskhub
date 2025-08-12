#!/usr/bin/env python3
"""
Create correct database file for scheduler
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def init_scheduler_database():
    """Initialize database used by scheduler"""
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Connect to scheduler database
    db_path = data_dir / "taskhub_default.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create hunters table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hunters (
        id TEXT PRIMARY KEY,
        skills TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        current_tasks TEXT DEFAULT '[]',
        completed_tasks INTEGER DEFAULT 0,
        failed_tasks INTEGER DEFAULT 0,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        last_read_discussion_timestamp TEXT
    )
    ''')
    
    # Create tasks table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        details TEXT NOT NULL,
        required_skill TEXT NOT NULL,
        status TEXT NOT NULL,
        hunter_id TEXT,
        lease_id TEXT,
        lease_expires_at TEXT,
        depends_on TEXT DEFAULT '[]',
        parent_task_id TEXT,
        published_by_hunter_id TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        evaluation TEXT,
        is_archived INTEGER DEFAULT 0
    )
    ''')
    
    # Create reports table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        hunter_id TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT,
        result TEXT,
        evaluation TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (hunter_id) REFERENCES hunters (id)
    )
    ''')
    
    # Create discussion_messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS discussion_messages (
        id TEXT PRIMARY KEY,
        hunter_id TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (hunter_id) REFERENCES hunters (id)
    )
    ''')
    
    # Create knowledge_items table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_items (
        id TEXT PRIMARY KEY,
        domain_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        content_type TEXT NOT NULL DEFAULT 'text',
        tags TEXT DEFAULT '[]',
        created_by_hunter_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        is_archived INTEGER DEFAULT 0
    )
    ''')
    
    # Create knowledge_domains table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS knowledge_domains (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        created_by_hunter_id TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_hunter_id ON tasks(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_task_id ON reports(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_hunter_id ON reports(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_discussion_hunter_id ON discussion_messages(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_items_domain_id ON knowledge_items(domain_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_items_created_by ON knowledge_items(created_by_hunter_id)')
    
    # Insert test data
    now = datetime.now().isoformat()
    
    # Insert system hunter
    cursor.execute('''
    INSERT OR IGNORE INTO hunters (id, skills, status, current_tasks, completed_tasks, 
                                  failed_tasks, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('system', json.dumps(['system', 'admin']), 'active', '[]', 0, 0, now, now))
    
    # Insert admin hunter
    cursor.execute('''
    INSERT OR IGNORE INTO hunters (id, skills, status, current_tasks, completed_tasks, 
                                  failed_tasks, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', json.dumps(['admin', 'management']), 'active', '[]', 0, 0, now, now))
    
    # Commit transaction
    conn.commit()
    conn.close()
    
    print(f"✅ Scheduler database initialization completed: {db_path}")
    print("📊 Created tables:")
    print("  - hunters (hunters)")
    print("  - tasks (tasks)")
    print("  - reports (reports)")
    print("  - discussion_messages (discussion messages)")
    print("  - knowledge_items (knowledge items)")
    print("  - knowledge_domains (knowledge domains)")
    print("👥 Test data: system, admin hunters created")

if __name__ == "__main__":
    init_scheduler_database()