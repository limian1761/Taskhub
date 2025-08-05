"""
Hunter-related tools for the Taskhub system.
"""

import logging
from typing import Any, cast

from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext
from taskhub.services import (
    hunter_register,
    hunter_study,
    get_hunter
)
from taskhub.context import get_store

logger = logging.getLogger(__name__)


def register_hunter_tools(app):
    """Register all hunter-related tools with the FastMCP app."""
    
    @app.tool("taskhub.hunter.register")
    async def register_hunter_tool(ctx: Context, skills: dict[str, int] | None = None) -> dict[str, Any]:
        """Register a new hunter with optional initial skills.
        
        This tool registers a new hunter in the system with an optional set of initial skills.
        If the hunter already exists, it will update their skills. This is typically called
        when a hunter first connects to the system.
        
        Args:
            ctx: The MCP context containing session information.
            skills: Optional dictionary mapping skill names to initial skill levels (0-100).
            
        Returns:
            A dictionary representation of the registered hunter object, along with the system guide.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        hunter = await hunter_register(store, hunter_id, skills)
        
        # 获取系统指南
        from taskhub.services.system_service import get_system_guide
        system_guide = await get_system_guide()
        
        # 返回猎人信息和系统指南
        result = hunter.model_dump()
        result["system_guide"] = system_guide
        return result

    @app.tool("taskhub.hunter.study")
    async def study(ctx: Context, knowledge_id: str) -> dict[str, Any]:
        """Study a knowledge item to improve skills.
        
        This tool allows a hunter to study a knowledge item, which will increase their
        skill levels in the areas covered by that knowledge. This is the primary mechanism
        for hunters to improve their capabilities and qualify for more complex tasks.
        
        Args:
            ctx: The MCP context containing session information.
            knowledge_id: The unique identifier of the knowledge item to study.
            
        Returns:
            A dictionary representation of the updated hunter object with improved skills.
            
        Raises:
            ValueError: If the hunter or knowledge item is not found.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        hunter = await hunter_study(store, hunter_id, knowledge_id)
        return hunter.model_dump()

    @app.resource("hunter://current")
    async def get_hunter_resource() -> dict[str, Any]:
        """Get current hunter resource.
        
        Returns:
            A dictionary representation of the hunter object.
        """
        # 由于资源函数不能直接访问上下文，我们返回一个默认的响应
        # 实际项目中，这应该通过其他方式实现
        return {
            "id": "default_hunter",
            "skills": {},
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z"
        }