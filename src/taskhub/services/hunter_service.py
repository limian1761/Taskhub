"""
Hunter-related service functions for the Taskhub system.
"""

import logging
from datetime import datetime, timezone

from taskhub.models.hunter import Hunter
from taskhub.models.knowledge import KnowledgeItem
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def hunter_register(store: SQLiteStore, hunter_id: str, skills: dict[str, int] | None = None) -> Hunter:
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        hunter = Hunter(id=hunter_id, skills=skills or {})
        await store.save_hunter(hunter)
    elif skills:
        for skill, level in skills.items():
            hunter.skills[skill] = level
        await store.save_hunter(hunter)
    return hunter


async def hunter_study(store: SQLiteStore, hunter_id: str, knowledge_id: str) -> Hunter:
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter not found: {hunter_id}")

    knowledge = await store.get_knowledge_item(knowledge_id)
    if not knowledge:
        raise ValueError(f"Knowledge item not found: {knowledge_id}")

    for skill in knowledge.skill_tags:
        if skill in hunter.skills:
            hunter.skills[skill] = min(100, hunter.skills[skill] + 5)
        else:
            hunter.skills[skill] = min(100, 5)

    await store.save_hunter(hunter)
    return hunter


async def get_hunter(store: SQLiteStore, hunter_id: str) -> Hunter | None:
    """Get a hunter by ID.
    
    Args:
        store: The database store.
        hunter_id: The ID of the hunter to retrieve.
        
    Returns:
        The hunter if found, None otherwise.
    """
    return await store.get_hunter(hunter_id)


async def hunter_list(store: SQLiteStore) -> list[Hunter]:
    return await store.list_hunters()
