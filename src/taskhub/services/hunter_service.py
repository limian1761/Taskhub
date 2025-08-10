"""
Hunter-related service functions for the Taskhub system.
"""

import logging
from datetime import datetime, timezone

from taskhub.models.hunter import Hunter
from taskhub.services import knowledge_service
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def hunter_register(store: SQLiteStore, hunter_id: str, skills: dict[str, int] | None = None) -> Hunter:
    """
    Register a new hunter or update an existing hunter's skills.

    If the hunter already exists, their existing information is preserved and
    new skills are added to their existing skills without overwriting them.
    
    This function can be used in two scenarios:
    1. Registering a new hunter with initial skills
    2. Updating an existing hunter's skills when they need to qualify for new tasks
    
    When skills are provided and the hunter already exists, the new skills are merged with
    existing skills. If a skill already exists, the higher value is kept. This ensures that
    hunters don't lose progress when updating their skills.

    Args:
        store: The database store
        hunter_id: The unique identifier for the hunter
        skills: Optional dictionary of skills to add to the hunter

    Returns:
        The registered or updated hunter
    """
    # 检查猎人是否已经存在
    hunter = await store.get_hunter(hunter_id)

    if not hunter:
        # 如果猎人不存在，创建新猎人
        logger.info(f"Creating new hunter with ID: {hunter_id}")
        hunter = Hunter(id=hunter_id, skills=skills or {})
    else:
        # 如果猎人已存在，更新技能
        logger.info(f"Updating skills for existing hunter {hunter_id}")
        if skills:
            # 合并技能，保留较高的技能值
            for skill_name, skill_level in skills.items():
                if skill_name in hunter.skills:
                    # 如果技能已存在，保留较高的值
                    hunter.skills[skill_name] = max(hunter.skills[skill_name], skill_level)
                    logger.debug(f"Updated {hunter_id}'s {skill_name} skill to {hunter.skills[skill_name]}")
                else:
                    # 如果是新技能，直接添加
                    hunter.skills[skill_name] = skill_level
                    logger.debug(f"Added new skill {skill_name} with level {skill_level} to hunter {hunter_id}")
        
        # 更新时间戳
        hunter.updated_at = datetime.now()

    await store.save_hunter(hunter)
    return hunter


async def hunter_study(store: SQLiteStore, hunter_id: str, knowledge_id: str) -> Hunter:
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter not found: {hunter_id}")

    knowledge = await knowledge_service.knowledge_get(knowledge_id)
    if not knowledge:
        raise ValueError(f"Knowledge item not found: {knowledge_id}")

    # Assuming the knowledge dictionary has a 'tags' key with a list of skill strings
    skill_tags = knowledge.get("tags", [])

    for skill in skill_tags:
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


async def adjust_hunter_reputation(store: SQLiteStore, hunter_id: str, new_reputation: int) -> Hunter:
    """Manually adjust a hunter's reputation."""
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter with ID {hunter_id} not found.")

    hunter.reputation = new_reputation
    await store.save_hunter(hunter)
    logger.info(f"Admin adjusted reputation for hunter {hunter_id} to {new_reputation}")
    return hunter


async def delete_hunter(store: SQLiteStore, hunter_id: str) -> None:
    """Delete a hunter from the database."""
    await store.delete_hunter(hunter_id)
    logger.info(f"Hunter {hunter_id} deleted from the database")


async def delete_all_hunters(store: SQLiteStore) -> None:
    """Delete all hunters from the database."""
    await store.delete_all_hunters()
    logger.info("All hunters deleted from the database")


async def find_best_hunter_for_task(
    store: SQLiteStore, skill: str, exclude_hunter_ids: list[str]
) -> Hunter | None:
    """
    Finds the most suitable hunter for a task based on skill, reputation, and current workload.
    
    Args:
        store: The database store
        skill: The required skill for the task
        exclude_hunter_ids: List of hunter IDs to exclude from consideration
        
    Returns:
        The best matching hunter, or None if no suitable hunter is found
    """
    all_hunters = await store.list_hunters()

    eligible_hunters = []
    for hunter in all_hunters:
        if (
            hunter.id not in exclude_hunter_ids
            and hunter.status == "active"
            and skill in hunter.skills
            and hunter.skills[skill] > 0  # 确保技能水平大于0
        ):
            eligible_hunters.append(hunter)

    if not eligible_hunters:
        logger.warning(f"No eligible hunters found for skill '{skill}' excluding {exclude_hunter_ids}")
        return None

    # Scoring algorithm: 70% reputation, 30% penalty for workload
    best_hunter = max(
        eligible_hunters,
        key=lambda h: (h.reputation * 0.7) - (len(h.current_tasks) * 0.3)
    )

    logger.info(f"Best hunter found for skill '{skill}': {best_hunter.id} with reputation {best_hunter.reputation}")
    return best_hunter
