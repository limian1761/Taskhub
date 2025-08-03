from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.tools.taskhub import (
    agent_register,
    agent_study,
    domain_create,
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
    domain = await domain_create(db, domain_name, domain_description)
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
        domain_tags=[domain.id],
        created_by="test-admin",
    )
    assert knowledge_item is not None
    assert domain.id in knowledge_item.domain_tags

    retrieved_knowledge = await db.get_knowledge_item(knowledge_item.id)
    assert retrieved_knowledge is not None
    assert retrieved_knowledge.title == knowledge_title


@pytest.mark.asyncio
async def test_agent_study(db: SQLiteStore):
    agent = await agent_register(db, "test-agent", "test-agent", ["python"])
    domain = await domain_create(db, "Machine Learning", "ML concepts.")
    knowledge = await knowledge_add(db, "Scikit-learn", "...", "web", [domain.id], "admin")

    updated_agent = await agent_study(db, agent.id, knowledge.id)
    assert updated_agent is not None
    assert updated_agent.domain_scores.get(domain.id, 0.0) > 0
