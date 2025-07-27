import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path

from src.models.task import Task, TaskCreateRequest
from src.models.agent import Agent
from src.storage.json_store import JsonStore
from src.tools.taskhub import (
    task_list, task_claim, report_submit, task_publish,
    TaskListParams, TaskClaimParams, ReportSubmitParams, TaskPublishParams
)


@pytest.fixture
def temp_store():
    """创建临时存储用于测试"""
    temp_dir = tempfile.mkdtemp()
    store = JsonStore(temp_dir)
    yield store
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_task_data():
    """示例任务数据"""
    return {
        "name": "测试任务",
        "details": "这是一个测试任务",
        "capability": "python"
    }


@pytest.fixture
def sample_agent_data():
    """示例代理数据"""
    return {
        "id": "agent-001",
        "name": "测试代理",
        "capabilities": ["python", "javascript"]
    }


@pytest.mark.asyncio
async def test_task_publish(temp_store):
    """测试任务创建"""
    params = TaskPublishParams(
        name="测试任务",
        details="测试详情",
        capability="python"
    )
    
    result = await task_publish(params)
    
    assert result["success"] is True
    assert "task_id" in result
    assert result["task"]["name"] == "测试任务"
    assert result["task"]["status"] == "pending"


@pytest.mark.asyncio
async def test_task_list_empty(temp_store):
    """测试空任务列表"""
    params = TaskListParams()
    tasks = await task_list(params)
    
    assert isinstance(tasks, list)
    assert len(tasks) == 0


@pytest.mark.asyncio
async def test_task_list_with_tasks(temp_store):
    """测试带任务的任务列表"""
    # 创建测试任务
    task = Task(
        id="test-001",
        name="测试任务",
        details="测试详情",
        capability="python"
    )
    temp_store.save_task(task)
    
    params = TaskListParams()
    tasks = await task_list(params)
    
    assert len(tasks) == 1
    assert tasks[0]["id"] == "test-001"


@pytest.mark.asyncio
async def test_task_claim_success(temp_store):
    """测试成功的任务认领"""
    # 创建测试任务和代理
    task = Task(
        id="task-001",
        name="测试任务",
        details="测试详情",
        capability="python"
    )
    temp_store.save_task(task)
    
    agent = Agent(
        id="agent-001",
        name="测试代理",
        capabilities=["python"]
    )
    temp_store.save_agent(agent)
    
    params = TaskClaimParams(
        task_id="task-001",
        agent_id="agent-001"
    )
    
    result = await task_claim(params)
    
    assert result["success"] is True
    assert result["task_id"] == "task-001"
    assert "lease_id" in result


@pytest.mark.asyncio
async def test_task_claim_nonexistent_task(temp_store):
    """测试认领不存在的任务"""
    params = TaskClaimParams(
        task_id="nonexistent",
        agent_id="agent-001"
    )
    
    result = await task_claim(params)
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_report_submit_success(temp_store):
    """测试成功的任务更新"""
    # 创建测试任务
    task = Task(
        id="task-001",
        name="测试任务",
        details="测试详情",
        capability="python",
        status="claimed",
        assignee="agent-001"
    )
    temp_store.save_task(task)
    
    params = ReportSubmitParams(
        task_id="task-001",
        status="completed",
        result="任务完成"
    )
    
    result = await report_submit(params)
    
    assert result["success"] is True
    assert result["task_id"] == "task-001"


@pytest.mark.asyncio
async def test_report_submit_nonexistent_task(temp_store):
    """测试更新不存在的任务"""
    params = ReportSubmitParams(
        task_id="nonexistent",
        status="completed"
    )
    
    result = await report_submit(params)
    
    assert result["success"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_task_filter_by_status(temp_store):
    """测试按状态过滤任务"""
    # 创建不同状态的任务
    pending_task = Task(
        id="pending-001",
        name="待处理任务",
        details="待处理",
        capability="python",
        status="pending"
    )
    completed_task = Task(
        id="completed-001",
        name="已完成任务",
        details="已完成",
        capability="python",
        status="completed"
    )
    
    temp_store.save_task(pending_task)
    temp_store.save_task(completed_task)
    
    # 测试过滤
    params = TaskListParams(status="pending")
    tasks = await task_list(params)
    
    assert len(tasks) == 1
    assert tasks[0]["id"] == "pending-001"


@pytest.mark.asyncio
async def test_task_filter_by_capability(temp_store):
    """测试按能力过滤任务"""
    # 创建不同能力的任务
    python_task = Task(
        id="python-001",
        name="Python任务",
        details="Python任务",
        capability="python"
    )
    js_task = Task(
        id="js-001",
        name="JavaScript任务",
        details="JavaScript任务",
        capability="javascript"
    )
    
    temp_store.save_task(python_task)
    temp_store.save_task(js_task)
    
    # 测试过滤
    params = TaskListParams(capability="python")
    tasks = await task_list(params)
    
    assert len(tasks) == 1
    assert tasks[0]["id"] == "python-001"


@pytest.mark.asyncio
async def test_task_with_dependencies(temp_store):
    """测试带依赖关系的任务"""
    # 创建依赖任务
    dep_task = Task(
        id="dep-001",
        name="依赖任务",
        details="依赖任务",
        capability="python",
        status="completed"
    )
    main_task = Task(
        id="main-001",
        name="主任务",
        details="主任务",
        capability="python",
        depends_on=["dep-001"]
    )
    
    temp_store.save_task(dep_task)
    temp_store.save_task(main_task)
    
    # 应该能列出主任务，因为依赖已完成
    params = TaskListParams()
    tasks = await task_list(params)
    
    assert len(tasks) == 1
    assert tasks[0]["id"] == "main-001"


if __name__ == "__main__":
    pytest.main([__file__])