from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from taskhub.models.hunter import Hunter
from taskhub.models.task import Task
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import (
    hunter_register,
    domain_create,
    task_delete,
    task_publish,
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
