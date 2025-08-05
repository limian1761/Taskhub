"""
Knowledge-related tools for the Taskhub system.
"""

import logging
from typing import Any, cast

from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext
from taskhub.services import (
    knowledge_add,
    knowledge_list,
    knowledge_search,
    get_system_guide
)
from taskhub.context import get_store


logger = logging.getLogger(__name__)


def register_knowledge_tools(app):
    """Register all knowledge-related tools with the FastMCP app."""
    
    @app.tool("taskhub.knowledge.add")
    async def add_knowledge(
        ctx: Context, title: str, content: str, source: str, skill_tags: list[str], created_by: str
    ) -> dict[str, Any]:
        """Add a new knowledge item to the system.
        
        This tool allows administrators or content creators to add new knowledge items
        to the system. These knowledge items can be studied by hunters to improve their skills.
        
        Args:
            ctx: The MCP context containing session information.
            title: The title or name of the knowledge item.
            content: The main content of the knowledge item.
            source: The source or origin of this knowledge.
            skill_tags: A list of skill names that this knowledge item relates to.
            created_by: The identifier of the user who created this knowledge item.
            
        Returns:
            A dictionary representation of the newly created knowledge item.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        knowledge_item = await knowledge_add(store, title, content, source, skill_tags, created_by)
        return knowledge_item.model_dump()

    @app.tool("taskhub.knowledge.list")
    async def list_knowledge(ctx: Context, skill_tag: str | None = None) -> list[dict[str, Any]]:
        """List knowledge items with optional skill tag filtering.
        
        This tool retrieves a list of knowledge items available in the system. It can be
        filtered to show only items related to a specific skill, which is useful for
        hunters looking to improve in a particular area.
        
        Args:
            ctx: The MCP context containing session information.
            skill_tag: Optional filter to only show knowledge items related to this skill.
            
        Returns:
            A list of dictionary representations of knowledge items.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        items = await knowledge_list(store, skill_tag)
        return [item.model_dump() for item in items]

    @app.tool("taskhub.knowledge.search")
    async def search_knowledge(ctx: Context, query: str, limit: int = 20) -> list[dict[str, Any]]:
        """Search for knowledge items by keyword.
        
        This tool allows hunters to search through knowledge items by keyword, making it
        easier to find relevant learning materials. The search looks through titles, content,
        and tags of knowledge items.
        
        Args:
            ctx: The MCP context containing session information.
            query: The search query string to match against knowledge items.
            limit: Maximum number of results to return (default: 20).
            
        Returns:
            A list of dictionary representations of knowledge items matching the search query.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        items = await knowledge_search(store, query, limit)
        return [item.model_dump() for item in items]

    @app.tool("taskhub.system.get_guide")
    async def get_system_guide_tool(ctx: Context) -> str:
        """Retrieve the system guide for hunters.
        
        This tool provides hunters with a comprehensive guide to using the Taskhub system,
        including information about available tools, workflow processes, and best practices.
        
        Args:
            ctx: The MCP context containing session information.
            
        Returns:
            A string containing the complete system guide.
        """
        await ctx.info("Hunter requested the system guide.")
        return await get_system_guide()