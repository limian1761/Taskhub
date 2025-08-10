from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import (
    hunter_register,
    hunter_study,
    create_domain,
    knowledge_add,
)


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[SQLiteStore, None]:
    """创建一个临时的内存数据库用于测试"""
    store = SQLiteStore(db_path=":memory:")
    await store.connect()
    yield store
    await store.close()


@pytest.mark.asyncio
async def test_domain_and_knowledge_creation(db: SQLiteStore):
    domain_name = "Data Science"
    domain_description = "Knowledge about data science."
        domain = await create_domain(db, domain_name, domain_description)
    assert domain is not None
    assert domain.name == domain_name

    retrieved_domain = await db.get_domain(domain.id)
    assert retrieved_domain is not None
    assert retrieved_domain.name == domain_name

    knowledge_title = "Pandas Basics"
    knowledge_item = await knowledge_add(
        db,
        title=knowledge_title,
        content="...",
        source="internal",
        skill_tags=[domain.name],  # 使用skill_tags而不是domain_tags
        created_by="test-admin",
    )
    assert knowledge_item is not None
    assert domain.name in knowledge_item.skill_tags

    retrieved_knowledge = await db.get_knowledge_item(knowledge_item.id)
    assert retrieved_knowledge is not None
    assert retrieved_knowledge.title == knowledge_title


@pytest.mark.asyncio
async def test_hunter_study(db: SQLiteStore):
    # 传递一个字典而不是列表作为skills参数
    hunter = await hunter_register(db, "test-hunter", {"python": 50})
        domain = await create_domain(db, "Machine Learning", "ML concepts.")
    knowledge = await knowledge_add(db, "Scikit-learn", "...", "web", [domain.name], "admin")

    updated_hunter = await hunter_study(db, hunter.id, knowledge.id)
    assert updated_hunter is not None
    assert updated_hunter.skills.get(domain.name, 0) > 0