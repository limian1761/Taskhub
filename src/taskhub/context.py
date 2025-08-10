"""
Context management for the Taskhub system.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Optional, Dict
import contextvars

from mcp.server.fastmcp import Context

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import system_service
from taskhub.utils.scheduler_utils import run_stale_task_check
from taskhub.utils.config import config

logger = logging.getLogger(__name__)

# Context variables for request-scoped data
namespace_ctx: contextvars.ContextVar[str] = contextvars.ContextVar('namespace', default='default')
hunter_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar('hunter_id', default='system')

@dataclass
class TaskhubAppContext:
    """Application context for the Taskhub system."""
    namespace_store: SQLiteStore
    current_namespace: str
    current_hunter_id: str
    
    async def close(self):
        """Close all database connections."""
        if self.namespace_store:
            await self.namespace_store.close()

def get_store() -> SQLiteStore:
    """Get the store for the current namespace."""
    if _app_context is None:
        raise RuntimeError("App context not initialized")
    
    # For now, we use the global app context store
    # The namespace is handled by the database path configuration
    return _app_context.namespace_store

# Cache for namespace-specific stores
_namespace_stores: dict[str, SQLiteStore] = {}

async def get_namespace_store(namespace: str = None) -> SQLiteStore:
    """Get or create a store for the specified namespace.
    
    Args:
        namespace: The namespace to use. If None, uses current request namespace.
        
    Returns:
        SQLiteStore instance for the namespace.
    """
    if namespace is None:
        namespace = "default"
    
    if namespace in _namespace_stores:
        return _namespace_stores[namespace]
    
    # Create new store for this namespace
    db_path = config.get_database_path(namespace)
    store = SQLiteStore(db_path)
    await store.connect()
    
    _namespace_stores[namespace] = store
    logger.info(f"Created new store for namespace: {namespace}")
    return store

async def close_namespace_store(namespace: str):
    """Close and remove the store for a specific namespace."""
    if namespace in _namespace_stores:
        store = _namespace_stores.pop(namespace)
        await store.close()
        logger.info(f"Closed store for namespace: {namespace}")

async def close_all_namespace_stores():
    """Close all namespace stores."""
    for namespace, store in list(_namespace_stores.items()):
        await store.close()
        logger.info(f"Closed store for namespace: {namespace}")
    _namespace_stores.clear()

@dataclass
class AppContext:
    """Complete application context including namespace and hunter ID."""
    namespace: str
    hunter_id: str
    store: SQLiteStore
    
    async def close(self):
        """Close the store connection."""
        if self.store:
            await self.store.close()

async def get_app_context(ctx: Context) -> AppContext:
    """Get the current application context with namespace and hunter ID."""

    print(ctx.request_context.request.headers)
    hunter_id = ctx.request_context.request.headers["hunter_id"]
    if not hunter_id:
        raise ValueError("hunter_id header is required")
    namespace = ctx.request_context.request.headers["taskhub_namespace"]
    if not namespace:
        raise ValueError("namespace header is required")
    store = await get_namespace_store(namespace)
    
    return AppContext(
        namespace=namespace,
        hunter_id=hunter_id,
        store=store
    )

@asynccontextmanager
async def taskhub_lifespan(namespace: str = None, hunter_id: str = None):
    """Application lifespan context manager with namespace and hunter ID."""
    global _app_context, _current_namespace, _current_hunter_id
    
    # Use provided values or current ones
    if namespace:
        _current_namespace = namespace
    if hunter_id:
        _current_hunter_id = hunter_id
    
    try:
        # Initialize stores with namespace
        db_path = config.get_database_path(_current_namespace)
        
        namespace_store = SQLiteStore(db_path)
        await namespace_store.connect()
        
        _app_context = TaskhubAppContext(
            namespace_store=namespace_store,
            current_namespace=_current_namespace,
            current_hunter_id=_current_hunter_id
        )
        
        logger.info(f"Taskhub app context initialized - namespace: {_current_namespace}, hunter_id: {_current_hunter_id}")
        
        # Start stale task check scheduler
        stale_task_task = asyncio.create_task(run_stale_task_check())
        
        yield _app_context
        
    finally:
        # Cancel stale task check
        stale_task_task.cancel()
        try:
            await stale_task_task
        except asyncio.CancelledError:
            pass
        
        # Close context
        if _app_context:
            await _app_context.close()
            _app_context = None
        
        logger.info("Taskhub app context closed")