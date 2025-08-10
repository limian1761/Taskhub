# MCP实战教程：从入门到精通

## 教程概述

本教程将带你从零开始构建一个完整的MCP（Model Context Protocol）服务器，并通过实际案例掌握MCP开发的核心技能。

## 项目准备

### 环境要求
- Python 3.8+
- FastMCP库
- FastAPI（可选，用于HTTP API）
- SQLite（数据存储）

### 安装依赖
```bash
pip install fastmcp fastapi uvicorn sqlalchemy
```

## 实战项目：任务管理MCP服务器

### 第一步：创建基础结构

创建项目目录结构：
```
task-manager-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py          # MCP服务器主文件
│   ├── models.py          # 数据模型
│   ├── services.py        # 业务逻辑
│   └── database.py        # 数据库连接
├── tests/
│   └── test_server.py
├── requirements.txt
└── README.md
```

### 第二步：实现数据模型

`models.py`:
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    status = Column(String, default="pending")  # pending, in_progress, completed
    priority = Column(Integer, default=1)  # 1-5
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
```

### 第三步：数据库连接

`database.py`:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建数据库表
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 第四步：业务逻辑实现

`services.py`:
```python
from sqlalchemy.orm import Session
from .models import Task
from typing import List, Optional

class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_task(self, title: str, description: str = "", priority: int = 1) -> Task:
        task = Task(title=title, description=description, priority=priority)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_task(self, task_id: int) -> Optional[Task]:
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_all_tasks(self) -> List[Task]:
        return self.db.query(Task).all()
    
    def update_task_status(self, task_id: int, status: str) -> Optional[Task]:
        task = self.get_task(task_id)
        if task:
            task.status = status
            self.db.commit()
            self.db.refresh(task)
        return task
    
    def delete_task(self, task_id: int) -> bool:
        task = self.get_task(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False
    
    def get_tasks_by_status(self, status: str) -> List[Task]:
        return self.db.query(Task).filter(Task.status == status).all()
    
    def get_high_priority_tasks(self) -> List[Task]:
        return self.db.query(Task).filter(Task.priority >= 4).all()
```

### 第五步：MCP服务器实现

`server.py`:
```python
from fastmcp import FastMCP
from .database import get_db
from .services import TaskService
from typing import List, Dict, Any

# 创建MCP服务器实例
mcp = FastMCP("TaskManager", version="1.0.0")

@mcp.tool()
def create_task(title: str, description: str = "", priority: int = 1) -> Dict[str, Any]:
    """创建新任务
    
    Args:
        title: 任务标题
        description: 任务描述（可选）
        priority: 优先级 1-5（默认1）
    
    Returns:
        创建的任务信息
    """
    db = next(get_db())
    service = TaskService(db)
    task = service.create_task(title, description, priority)
    return task.to_dict()

@mcp.tool()
def get_task(task_id: int) -> Dict[str, Any]:
    """根据ID获取任务详情
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务详细信息，如果未找到返回None
    """
    db = next(get_db())
    service = TaskService(db)
    task = service.get_task(task_id)
    return task.to_dict() if task else None

@mcp.tool()
def get_all_tasks() -> List[Dict[str, Any]]:
    """获取所有任务列表
    
    Returns:
        任务列表
    """
    db = next(get_db())
    service = TaskService(db)
    tasks = service.get_all_tasks()
    return [task.to_dict() for task in tasks]

@mcp.tool()
def update_task_status(task_id: int, status: str) -> Dict[str, Any]:
    """更新任务状态
    
    Args:
        task_id: 任务ID
        status: 新状态（pending/in_progress/completed）
    
    Returns:
        更新后的任务信息
    """
    db = next(get_db())
    service = TaskService(db)
    task = service.update_task_status(task_id, status)
    return task.to_dict() if task else None

@mcp.tool()
def delete_task(task_id: int) -> bool:
    """删除任务
    
    Args:
        task_id: 任务ID
    
    Returns:
        删除是否成功
    """
    db = next(get_db())
    service = TaskService(db)
    return service.delete_task(task_id)

@mcp.tool()
def get_tasks_by_status(status: str) -> List[Dict[str, Any]]:
    """根据状态获取任务列表
    
    Args:
        status: 任务状态
    
    Returns:
        符合条件的任务列表
    """
    db = next(get_db())
    service = TaskService(db)
    tasks = service.get_tasks_by_status(status)
    return [task.to_dict() for task in tasks]

@mcp.tool()
def get_high_priority_tasks() -> List[Dict[str, Any]]:
    """获取高优先级任务（优先级>=4）
    
    Returns:
        高优先级任务列表
    """
    db = next(get_db())
    service = TaskService(db)
    tasks = service.get_high_priority_tasks()
    return [task.to_dict() for task in tasks]

@mcp.tool()
def get_task_statistics() -> Dict[str, Any]:
    """获取任务统计信息
    
    Returns:
        任务统计信息
    """
    db = next(get_db())
    service = TaskService(db)
    
    all_tasks = service.get_all_tasks()
    total_tasks = len(all_tasks)
    
    status_counts = {}
    for task in all_tasks:
        status_counts[task.status] = status_counts.get(task.status, 0) + 1
    
    high_priority_count = len(service.get_high_priority_tasks())
    
    return {
        "total_tasks": total_tasks,
        "status_distribution": status_counts,
        "high_priority_count": high_priority_count
    }

if __name__ == "__main__":
    mcp.run()
```

### 第六步：创建启动脚本

`run_server.py`:
```python
from src.server import mcp

if __name__ == "__main__":
    mcp.run()
```

### 第七步：测试用例

`tests/test_server.py`:
```python
import pytest
from src.server import mcp
from src.database import get_db
from src.services import TaskService

class TestTaskManagerMCP:
    
    @pytest.fixture
    def db(self):
        return next(get_db())
    
    @pytest.fixture
    def service(self, db):
        return TaskService(db)
    
    def test_create_task(self):
        result = mcp.call_tool("create_task", {
            "title": "测试任务",
            "description": "这是一个测试任务",
            "priority": 3
        })
        assert result["title"] == "测试任务"
        assert result["status"] == "pending"
    
    def test_get_task(self):
        # 先创建任务
        created = mcp.call_tool("create_task", {"title": "获取测试"})
        task_id = created["id"]
        
        # 再获取任务
        retrieved = mcp.call_tool("get_task", {"task_id": task_id})
        assert retrieved["id"] == task_id
        assert retrieved["title"] == "获取测试"
    
    def test_update_task_status(self):
        # 创建任务
        created = mcp.call_tool("create_task", {"title": "状态测试"})
        task_id = created["id"]
        
        # 更新状态
        updated = mcp.call_tool("update_task_status", {
            "task_id": task_id,
            "status": "completed"
        })
        assert updated["status"] == "completed"
    
    def test_delete_task(self):
        # 创建任务
        created = mcp.call_tool("create_task", {"title": "删除测试"})
        task_id = created["id"]
        
        # 删除任务
        deleted = mcp.call_tool("delete_task", {"task_id": task_id})
        assert deleted is True
        
        # 确认任务已删除
        retrieved = mcp.call_tool("get_task", {"task_id": task_id})
        assert retrieved is None
```

### 第八步：运行和测试

#### 启动MCP服务器
```bash
python run_server.py
```

#### 使用MCP Inspector测试
```bash
npx @modelcontextprotocol/inspector python run_server.py
```

#### 运行测试
```bash
pytest tests/test_server.py -v
```

## 进阶功能

### 1. 添加资源支持
```python
@mcp.resource("task://list")
async def get_task_resource():
    """以资源形式提供任务列表"""
    db = next(get_db())
    service = TaskService(db)
    tasks = service.get_all_tasks()
    return {"tasks": [task.to_dict() for task in tasks]}
```

### 2. 添加提示模板
```python
@mcp.prompt()
def task_summary_prompt():
    """生成任务汇总提示"""
    db = next(get_db())
    service = TaskService(db)
    stats = service.get_task_statistics()
    
    return f"""
    当前任务统计：
    - 总任务数：{stats['total_tasks']}
    - 状态分布：{stats['status_distribution']}
    - 高优先级任务：{stats['high_priority_count']}
    
    请分析当前任务管理情况并提供建议。
    """
```

### 3. 错误处理增强
```python
@mcp.tool()
def safe_create_task(title: str, description: str = "", priority: int = 1) -> Dict[str, Any]:
    """安全创建任务，包含参数验证"""
    if not title or len(title) < 2:
        raise ValueError("任务标题必须至少2个字符")
    
    if priority < 1 or priority > 5:
        raise ValueError("优先级必须在1-5之间")
    
    try:
        db = next(get_db())
        service = TaskService(db)
        task = service.create_task(title, description, priority)
        return {"success": True, "task": task.to_dict()}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## 部署建议

### Docker化部署
`Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY run_server.py .

EXPOSE 8000
CMD ["python", "run_server.py"]
```

### 监控和日志
```python
import logging
from fastmcp import FastMCP

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

mcp = FastMCP("TaskManager", version="1.0.0")

@mcp.tool()
def monitored_create_task(**kwargs):
    logging.info(f"创建任务：{kwargs}")
    # 实际逻辑...
```

## 总结

通过这个实战教程，你已经学会了：
1. MCP服务器的基本结构和配置
2. 如何定义和使用MCP工具
3. 数据库集成和业务逻辑分离
4. 测试用例的编写和执行
5. 高级功能如资源和提示模板
6. 部署和监控的最佳实践

继续探索更多MCP功能，构建更强大的AI应用！