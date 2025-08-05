"""
Knowledge-related service functions for the Taskhub system.
"""

import logging
import sys
from pathlib import Path

# Add src to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from taskhub.models.knowledge import KnowledgeItem
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def knowledge_add(
    store: SQLiteStore, title: str, content: str, source: str, skill_tags: list[str], created_by: str
) -> KnowledgeItem:
    knowledge_item = KnowledgeItem(
        id=generate_id("knowledge"),
        title=title,
        content=content,
        source=source,
        skill_tags=skill_tags,
        created_by=created_by,
    )
    await store.save_knowledge_item(knowledge_item)
    return knowledge_item


async def knowledge_search(store: SQLiteStore, query: str, limit: int = 20) -> list[KnowledgeItem]:
    return await store.search_knowledge(query, limit)


async def knowledge_list(store: SQLiteStore) -> list[KnowledgeItem]:
    return await store.list_knowledge_items()
