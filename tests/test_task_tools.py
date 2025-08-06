import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.models.task import Task, TaskStatus
from taskhub.tools.task_tools import register_task_tools
from taskhub.services import (
    task_publish,
    task_claim,
    task_start,
    task_complete,
    task_list,
    get_task,
    report_submit
)

# 创建一个模拟的FastMCP应用
class MockApp:
    def __init__(self):
        self.tools = {}
        self.resources = {}
    
    def tool(self, name=None):
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator
    
    def resource(self, pattern):
        def decorator(func):
            self.resources[pattern] = func
            return func
        return decorator

@pytest_asyncio.fixture
async def db():
    """创建一个临时的内存数据库用于测试"""
    store = SQLiteStore(db_path=":memory:")
    await store.connect()
    yield store
    await store.close()

@pytest_asyncio.fixture
async def mock_context():
    """创建一个模拟的MCP上下文"""
    context = MagicMock()
    context.session.hunter_id = "test-hunter"
    context.request_context = MagicMock()
    return context

@pytest_asyncio.fixture
def app():
    """创建一个模拟的应用实例"""
    return MockApp()

@pytest.mark.asyncio
async def test_publish_task_tool(db, mock_context, app, monkeypatch):
    """测试发布任务工具"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟task_publish函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "name": "Test Task"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.task_publish", AsyncMock(return_value=mock_task))
    
    # 调用工具函数
    publish_tool = app.tools["taskhub.task.publish"]
    result = await publish_tool(
        mock_context,
        name="Test Task",
        details="Test Details",
        required_skill="python"
    )
    
    # 验证结果
    assert result["id"] == "test-task-id"
    assert result["name"] == "Test Task"

@pytest.mark.asyncio
async def test_claim_task_tool(db, mock_context, app, monkeypatch):
    """测试认领任务工具"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟task_claim函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "status": "CLAIMED"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.task_claim", AsyncMock(return_value=mock_task))
    
    # 调用工具函数
    claim_tool = app.tools["taskhub.task.claim"]
    result = await claim_tool(mock_context, task_id="test-task-id")
    
    # 验证结果
    assert result["id"] == "test-task-id"
    assert result["status"] == "CLAIMED"

@pytest.mark.asyncio
async def test_start_task_tool(db, mock_context, app, monkeypatch):
    """测试开始任务工具"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟task_start函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "status": "IN_PROGRESS"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.task_start", AsyncMock(return_value=mock_task))
    
    # 调用工具函数
    start_tool = app.tools["taskhub.task.start"]
    result = await start_tool(mock_context, task_id="test-task-id")
    
    # 验证结果
    assert result["id"] == "test-task-id"
    assert result["status"] == "IN_PROGRESS"

@pytest.mark.asyncio
async def test_complete_task_tool(db, mock_context, app, monkeypatch):
    """测试完成任务工具"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟task_complete函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "status": "COMPLETED"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.task_complete", AsyncMock(return_value=mock_task))
    
    # 调用工具函数
    complete_tool = app.tools["taskhub.task.complete"]
    result = await complete_tool(mock_context, task_id="test-task-id", result="Test Result")
    
    # 验证结果
    assert result["id"] == "test-task-id"
    assert result["status"] == "COMPLETED"

@pytest.mark.asyncio
async def test_list_tasks_tool(db, mock_context, app, monkeypatch):
    """测试列出任务工具"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟task_list函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "name": "Test Task"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.task_list", AsyncMock(return_value=[mock_task]))
    
    # 调用工具函数
    list_tool = app.tools["taskhub.task.list"]
    result = await list_tool(mock_context)
    
    # 验证结果
    assert len(result) == 1
    assert result[0]["id"] == "test-task-id"

@pytest.mark.asyncio
async def test_get_task_resource(db, app, monkeypatch):
    """测试获取任务资源"""
    # 注册工具
    register_task_tools(app)
    
    # 模拟get_task函数
    mock_task = MagicMock()
    mock_task.id = "test-task-id"
    mock_task.model_dump.return_value = {"id": "test-task-id", "name": "Test Task"}
    
    monkeypatch.setattr("taskhub.tools.task_tools.get_task", AsyncMock(return_value=mock_task))
    
    # 模拟应用状态
    from taskhub.tools.task_tools import app as real_app
    real_app.state = MagicMock()
    real_app.state.stores = {"default": db}
    
    # 调用资源函数
    get_task_resource = app.resources["task://{task_id}"]
    result = await get_task_resource(task_id="test-task-id")
    
    # 验证结果
    assert result["id"] == "test-task-id"
    assert result["name"] == "Test Task"