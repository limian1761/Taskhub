"""
Discussion-related service functions for the Taskhub system.
"""
from datetime import datetime, timezone
from taskhub.models.discussion import DiscussionMessage
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

async def post_message(store: SQLiteStore, hunter_id: str, content: str) -> DiscussionMessage:
    """Creates and saves a new discussion message."""
    message = DiscussionMessage(
        id=generate_id("discussion"),
        hunter_id=hunter_id,
        content=content,
    )
    await store.save_discussion_message(message)
    return message

async def get_unread_messages(store: SQLiteStore, hunter_id: str) -> list[DiscussionMessage]:
    """Gets all unread messages for a given hunter."""
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        return []
    
    timestamp = hunter.last_read_discussion_timestamp or datetime.fromtimestamp(0, tz=timezone.utc)
    return await store.get_messages_after_timestamp(timestamp)

import logging

logger = logging.getLogger(__name__)

async def mark_as_read(store: SQLiteStore, hunter_id: str) -> None:
    """Mark discussion as read for a hunter by updating their last read timestamp.
    
    Args:
        store: The database store
        hunter_id: The ID of the hunter
    """
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter {hunter_id} not found")
    
    current_time = datetime.now(timezone.utc)
    await store.update_hunter_last_read_timestamp(hunter_id, current_time)
    
    # Also update the hunter object in memory
    hunter.last_read_discussion_timestamp = current_time
    await store.save_hunter(hunter)
    
    logger.info(f"Hunter {hunter_id} marked discussion as read at {current_time}")

async def get_all_messages(store: SQLiteStore) -> list[DiscussionMessage]:
    """Get all discussion messages.
    
    Args:
        store: The database store
        
    Returns:
        List of all DiscussionMessages
    """
    return await store.get_latest_messages(100)
