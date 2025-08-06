from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from taskhub.models.hunter import Hunter
from taskhub.models.task import Task
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import (
    hunter_register,
    task_delete,
    task_publish,
    domain_create,
)
# 从正确的模块导入domain_create
from taskhub.services import (
    hunter_register,
    task_delete,
    task_publish,
    domain_create,
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[SQLiteStore, None]:
    """创建一个临时的内存数据库用于测试"""
    store = SQLiteStore(db_path=":memory:")
    await store.connect()
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_hunter_register_updated(db: SQLiteStore):
    hunter_id = "test-hunter-001"
    skills = {"python": 80, "testing": 60}

    hunter = await hunter_register(
        db, hunter_id=hunter_id, skills=skills
    )

    assert isinstance(hunter, Hunter)
    assert hunter.id == hunter_id
    assert hunter.skills == skills


@pytest.mark.asyncio
async def test_hunter_register_preserves_existing_skills(db: SQLiteStore):
    """测试猎人注册时不会覆盖已有的技能，并且新技能会被正确添加"""
    hunter_id = "test-hunter-002"
    
    # 首先注册一个带有初始技能的猎人
    initial_skills = {"python": 80, "testing": 60}
    hunter = await hunter_register(
        db, hunter_id=hunter_id, skills=initial_skills
    )
    
    # 验证初始技能
    assert isinstance(hunter, Hunter)
    assert hunter.id == hunter_id
    assert hunter.skills == initial_skills
    
    # 再次注册同一个猎人，但这次带有不同的技能
    new_skills = {"javascript": 70, "html": 85}
    updated_hunter = await hunter_register(
        db, hunter_id=hunter_id, skills=new_skills
    )
    
    # 验证猎人还是同一个猎人
    assert isinstance(updated_hunter, Hunter)
    assert updated_hunter.id == hunter_id
    
    # 验证原有的技能没有被覆盖，并且新技能被添加了
    assert "python" in updated_hunter.skills
    assert "testing" in updated_hunter.skills
    assert "javascript" in updated_hunter.skills
    assert "html" in updated_hunter.skills
    
    # 验证原有技能的等级没有改变
    assert updated_hunter.skills["python"] == 80
    assert updated_hunter.skills["testing"] == 60
    
    # 验证新技能的等级正确
    assert updated_hunter.skills["javascript"] == 70
    assert updated_hunter.skills["html"] == 85


@pytest.mark.asyncio
async def test_task_publish_updated(db: SQLiteStore):
    domain = await domain_create(db, "Test Domain", "For task publishing test")

    task = await task_publish(
        db,
        name="Test Task",
        details="Details for the test task.",
        capability="python",
        required_domains=[domain.id],
        created_by="test-creator",
    )

    assert isinstance(task, Task)
    assert task.name == "Test Task"
    assert task.required_domains == [domain.id]

    retrieved_task = await db.get_task(task.id)
    assert retrieved_task is not None
    assert retrieved_task.required_domains == [domain.id]


@pytest.mark.asyncio
async def test_task_delete(db: SQLiteStore):
    domain = await domain_create(db, "Test Domain", "For task deleting test")

    task = await task_publish(
        db,
        name="Test Task to Delete",
        details="Details for the test task to delete.",
        capability="python",
        required_domains=[domain.id],
        created_by="test-creator",
    )

    assert task is not None
    retrieved_task = await db.get_task(task.id)
    assert retrieved_task is not None

    result = await task_delete(db, task_id=task.id, force=True)
    assert result is True

    deleted_task = await db.get_task(task.id)
    assert deleted_task is None