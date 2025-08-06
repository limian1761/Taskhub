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
        
        Note: Hunters' skills are associated with skill domains. In Taskhub, skills and domains 
        are the same concept but with different names used in different contexts:
        - "Skill" is used when referring to hunter abilities or task requirements
        - "Domain" is used when referring to knowledge areas or categories
        
        You can only specify skills that already exist in the system. If you need a new skill 
        domain, you must first create it using the domain creation tool.
        
        If you're an existing hunter looking to update your skills (for example, when your 
        current skills are insufficient for available tasks), you can call this tool with 
        new or updated skill values. Existing skills will be preserved, and new skills will 
        be added without overwriting existing ones.
        
        Args:
            ctx: The MCP context containing session information.
            skills: Optional dictionary mapping skill names to initial skill levels (0-100).
                   Skill names must be from existing skill domains in the system.
            
        Returns:
            A dictionary representation of the registered hunter object, along with the system guide.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        
        # 打印请求头信息
        request_context = cast(RequestContext, ctx.request_context)
        if request_context.request:
            headers = dict(request_context.request.headers)
            logger.info(f"Request headers: {headers}")
        
        logger.info(f"Registering hunter with ID: {hunter_id}")
        if skills:
            logger.debug(f"Initial skills for hunter {hunter_id}: {skills}")
        
        hunter = await hunter_register(store, hunter_id, skills)
        
        # 记录猎人注册成功
        logger.info(f"Hunter {hunter_id} registered successfully with reputation: {hunter.reputation}")
        
        # 获取系统指南
        from taskhub.services.system_service import get_system_guide
        system_guide = await get_system_guide()
        
        # 返回猎人信息和系统指南
        result = hunter.model_dump()
        result["system_guide"] = system_guide
        
        logger.debug(f"Returning hunter info for {hunter_id}")
        return result

    @app.tool("taskhub.hunter.study")
    async def study(ctx: Context, knowledge_id: str) -> dict[str, Any]:
        """Study a knowledge item to improve skills.
        
        This tool allows a hunter to study a knowledge item, which will increase their
        skill levels in the areas covered by that knowledge. This is the primary mechanism
        for hunters to improve their capabilities and qualify for more complex tasks.
        
        Note: Studying knowledge items will improve the hunter's skills in the corresponding
        skill domains. In Taskhub, skills and domains are the same concept but with different 
        names used in different contexts:
        - "Skill" is used when referring to hunter abilities or task requirements
        - "Domain" is used when referring to knowledge areas or categories
        
        Each knowledge item is tagged with one or more skill domains.
        
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
        
        logger.info(f"Hunter {hunter_id} is studying knowledge item: {knowledge_id}")
        
        hunter = await hunter_study(store, hunter_id, knowledge_id)
        
        logger.info(f"Hunter {hunter_id} successfully studied knowledge item {knowledge_id}")
        logger.debug(f"Updated hunter skills: {hunter.skills}")
        
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