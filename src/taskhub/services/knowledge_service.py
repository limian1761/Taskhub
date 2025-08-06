"""
Knowledge-related service functions for the Taskhub system.
"""

import logging
import sys
from pathlib import Path

# Add src to path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from taskhub.models.knowledge import KnowledgeItem
from taskhub.models.domain import Domain
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def knowledge_add(store: SQLiteStore, knowledge_id: str, content: str, title: str = None, source: str = "manual_add", skill_tags: list[str] = None, created_by: str = "system", status: str = None) -> KnowledgeItem:
    """Add a new knowledge item to the system.
    
    Args:
        store: The database store
        knowledge_id: The ID for the new knowledge item
        content: The content of the knowledge item
        title: The title of the knowledge item
        source: The source of the knowledge
        skill_tags: List of skill tags for the knowledge item
        created_by: The creator of the knowledge item
        status: The status of the knowledge item (draft or published)
        
    Returns:
        The created KnowledgeItem object
    """
    # Create knowledge item
    knowledge_item = KnowledgeItem(
        id=knowledge_id,
        title=title or f"Knowledge Item {knowledge_id}",
        content=content,
        source=source,
        skill_tags=skill_tags or [],
        created_by=created_by,
        status=status if status else "draft"
    )
    
    # Save to store
    await store.save_knowledge_item(knowledge_item)
    logger.info(f"Knowledge item {knowledge_id} added")
    return knowledge_item


async def knowledge_search(store: SQLiteStore, query: str, limit: int = 20) -> list[KnowledgeItem]:
    return await store.search_knowledge(query, limit)


async def knowledge_list(store: SQLiteStore) -> list[KnowledgeItem]:
    """List all knowledge items in the system.
    
    Args:
        store: The database store
        
    Returns:
        List of all KnowledgeItem objects
    """
    return await store.list_knowledge_items()


async def delete_all_knowledge(store: SQLiteStore) -> None:
    """Delete all knowledge items from the database."""
    await store.delete_all_knowledge_items()
    logger.info("All knowledge items deleted from the database")


async def delete_knowledge(store: SQLiteStore, knowledge_id: str) -> None:
    """Delete a knowledge item from the database."""
    await store.delete_knowledge_item(knowledge_id)
    logger.info(f"Knowledge item {knowledge_id} deleted from the database")


async def domain_create(store: SQLiteStore, name: str, description: str) -> Domain:
    """Create a new knowledge domain.
    
    In Taskhub, skills and domains are the same concept but with different names used in 
    different contexts:
    - "Skill" is used when referring to hunter abilities or task requirements
    - "Domain" is used when referring to knowledge areas or categories
    
    Creating a new domain effectively creates a new skill that hunters can learn and tasks
    can require. Before creating a new domain, make sure it doesn't already exist.
    
    Args:
        store: The database store to save the domain to
        name: The name of the new domain/skill (must be unique)
        description: A detailed description of what this domain/skill covers
        
    Returns:
        The newly created Domain object
    """
    domain = Domain(
        id=generate_id("domain"),
        name=name,
        description=description,
    )
    await store.save_domain(domain)
    return domain