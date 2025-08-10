#!/usr/bin/env python3
"""
完整的Taskhub数据库初始化脚本
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def init_database():
    """初始化完整的数据库结构"""
    
    # 确保data目录存在
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 连接到数据库
    db_path = data_dir / "taskhub.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建hunters表
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
    
    # 创建tasks表
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
    
    # 创建reports表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        hunter_id TEXT NOT NULL,
        content TEXT NOT NULL,
        evaluation TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        FOREIGN KEY (task_id) REFERENCES tasks (id),
        FOREIGN KEY (hunter_id) REFERENCES hunters (id)
    )
    ''')
    
    # 创建discussion_messages表
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
    
    # 创建knowledge_items表
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
    
    # 创建knowledge_domains表
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
    
    # 创建索引
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_hunter_id ON tasks(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_task_id ON reports(task_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_hunter_id ON reports(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_discussion_hunter_id ON discussion_messages(hunter_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_items_domain_id ON knowledge_items(domain_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_knowledge_items_created_by ON knowledge_items(created_by_hunter_id)')
    
    # 插入测试数据
    now = datetime.now().isoformat()
    
    # 插入system猎人
    cursor.execute('''
    INSERT OR IGNORE INTO hunters (id, skills, status, current_tasks, completed_tasks, 
                                  failed_tasks, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('system', json.dumps(['system', 'admin']), 'active', '[]', 0, 0, now, now))
    
    # 插入admin猎人
    cursor.execute('''
    INSERT OR IGNORE INTO hunters (id, skills, status, current_tasks, completed_tasks, 
                                  failed_tasks, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', json.dumps(['admin', 'management']), 'active', '[]', 0, 0, now, now))
    
    # 提交事务
    conn.commit()
    conn.close()
    
    print(f"数据库初始化完成: {db_path}")
    print("创建的表:")
    print("  - hunters (猎人)")
    print("  - tasks (任务)")
    print("  - reports (报告)")
    print("  - discussion_messages (讨论消息)")
    print("  - knowledge_items (知识项)")
    print("  - knowledge_domains (知识域)")
    print("测试数据: system, admin 猎人已创建")

if __name__ == "__main__":
    init_database()