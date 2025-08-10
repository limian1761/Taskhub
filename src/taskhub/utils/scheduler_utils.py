"""
Scheduler utilities for Taskhub system.

This module provides shared utilities for running scheduled tasks,
eliminating code duplication across different modules.
"""

import logging
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import system_service
from taskhub.utils.config import config

logger = logging.getLogger(__name__)


async def run_stale_task_check():
    """
    Scheduler job wrapper to create a store instance and run the stale task check.
    
    This function is designed to be used as a scheduled job that runs independently
    of the main application context. It creates its own database store instance
    and performs the stale task escalation check.
    
    Note: In multi-tenant scenarios, this uses the default namespace. For more
    complex multi-tenant setups, consider extending this function.
    """
    # Note: Scheduler jobs run independently and need their own store instance
    # We assume the default namespace is 'default' for multi-tenant scenarios
    db_path = config.get_database_path(config.get_default_namespace())
    store = SQLiteStore(db_path)
    await store.connect()
    try:
        await system_service.check_and_escalate_stale_tasks(store)
        logger.info("Successfully completed stale task check")
    except Exception as e:
        logger.error(f"Error during stale task check: {e}")
        raise
    finally:
        await store.close()