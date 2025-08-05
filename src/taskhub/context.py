"""
Application context and database store management for Taskhub.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

from mcp.server.fastmcp import FastMCP
from mcp.shared.context import RequestContext
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.config import config

logger = logging.getLogger(__name__)


@dataclass
class TaskhubAppContext:
    """Application context for Taskhub, managing database stores for different namespaces."""
    stores: dict[str, SQLiteStore] = field(default_factory=dict)
    
    def get_or_create_store(self, namespace: str) -> SQLiteStore:
        """Get or create a database store for the given namespace.
        
        Args:
            namespace: The namespace to get or create a store for.
            
        Returns:
            The SQLiteStore instance for the namespace.
        """
        if namespace not in self.stores:
            db_path = config.get_database_path(namespace)
            logger.info(f"Creating new database store for namespace '{namespace}' at {db_path}")
            self.stores[namespace] = SQLiteStore(db_path)
        else:
            logger.debug(f"Reusing existing database store for namespace '{namespace}'")
        return self.stores[namespace]
    
    async def close_stores(self):
        """Close all database stores."""
        for namespace, store in self.stores.items():
            logger.info(f"Closing database store for namespace '{namespace}'")
            await store.close()


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[TaskhubAppContext]:
    """Application lifespan manager, initializing and cleaning up resources.
    
    Args:
        server: The FastMCP server instance.
        
    Yields:
        The TaskhubAppContext instance.
    """
    logger.info("Initializing Taskhub application")
    ctx = TaskhubAppContext()
    server.state = ctx  # Attach the context to the app's state
    try:
        yield ctx
    finally:
        logger.info("Shutting down Taskhub application")
        for namespace, store in ctx.stores.items():
            logger.info(f"Closing database store for namespace '{namespace}'")
            await store.close()


def get_store(ctx: RequestContext[Any, TaskhubAppContext, Any]) -> SQLiteStore:
    """Get the database store for the current request's namespace.
    
    Args:
        ctx: The request context containing session information.
        
    Returns:
        The SQLiteStore instance for the current namespace.
    """
    # 1. 从配置中获取默认值作为基础
    namespace = config.get_default_namespace()
    hunter_id = config.get_default_hunter_id()
    
    # 2. 如果存在请求，则尝试从请求头中覆盖默认值
    if ctx.request:
        headers = {k.lower(): v for k, v in ctx.request.headers.items()}
        
        # 使用请求头中的值（如果存在），否则回退到默认值。
        # .get() 对缺失的键返回 None，因此 "or" 运算符可以简洁地实现这一点。
        namespace = headers.get("taskhub_namespace") or namespace
        hunter_id = headers.get("hunter_id") or hunter_id
    
    # 3. 将最终确定的值存储在会话中以供后续使用
    ctx.session.namespace = namespace
    ctx.session.hunter_id = hunter_id
    
    # 4. 记录请求上下文用于调试和监控
    if ctx.request:
        request_info = {
            "method": ctx.request.method,
            "url": str(ctx.request.url),
            "namespace": namespace,
            "hunter_id": hunter_id,
        }
        logging.getLogger("taskhub.request").info(f"Request context: {request_info}")
    
    # 5. 获取（或创建）指定命名空间的存储实例
    app_ctx = ctx.lifespan_context
    return app_ctx.get_or_create_store(namespace)