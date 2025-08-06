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
    domain_create,
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
        
        Note: Knowledge items are associated with skill domains. In Taskhub, skills and domains 
        are the same concept but with different names used in different contexts:
        - "Skill" is used when referring to hunter abilities or task requirements
        - "Domain" is used when referring to knowledge areas or categories
        
        You can only tag knowledge with skills that already exist in the system. If you need a 
        new skill domain, you must first create it using the domain creation tool.
        
        Args:
            ctx: The MCP context containing session information.
            title: The title or name of the knowledge item.
            content: The main content of the knowledge item.
            source: The source or origin of this knowledge.
            skill_tags: A list of skill names that this knowledge item relates to. Must be
                       from existing skill domains in the system.
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
        
        Note: Knowledge items are filtered by skill domains. In Taskhub, skills and domains 
        are the same concept but with different names used in different contexts:
        - "Skill" is used when referring to hunter abilities or task requirements
        - "Domain" is used when referring to knowledge areas or categories
        
        You can only filter by skills that already exist in the system.
        
        Args:
            ctx: The MCP context containing session information.
            skill_tag: Optional filter to only show knowledge items related to this skill.
                      Must be from existing skill domains in the system.
            
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

    @app.tool("taskhub.domain.create")
    async def create_domain(ctx: Context, name: str, description: str) -> dict[str, Any]:
        """Create a new skill domain.
        
        This tool allows administrators to create new skill domains in the system. In Taskhub, 
        skills and domains are the same concept but with different names used in different contexts:
        - "Skill" is used when referring to hunter abilities or task requirements
        - "Domain" is used when referring to knowledge areas or categories
        
        All tasks, knowledge items, and hunter skills must be associated with existing skill domains.
        
        Use this tool when you need to introduce a new area of expertise that doesn't fit into
        any existing skill domains. For example, if you need to create tasks or knowledge items
        related to a new technology or field.
        
        Args:
            ctx: The MCP context containing session information.
            name: The name of the new skill domain (must be unique). This will be used as the 
                 skill name when associating with hunters, tasks, and knowledge items.
            description: A detailed description of what this skill domain covers.
            
        Returns:
            A dictionary representation of the newly created domain object.
            
        Raises:
            ValueError: If a domain with the same name already exists.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        domain = await domain_create(store, name, description)
        return domain.model_dump()

    @app.tool("taskhub.knowledge.request_research")
    async def request_research_task(
        ctx: Context, 
        topic: str, 
        required_skill: str, 
        research_goal: str,
        details: str | None = None
    ) -> dict[str, Any]:
        """Request a research task to gather missing knowledge on a specific topic.
        
        This tool allows hunters to publish a research task when they identify a gap in the 
        knowledge base that prevents them from completing other tasks or improving their skills.
        
        When you encounter a situation where you need knowledge that doesn't exist in the system,
        you can use this tool to create a research task. Other hunters can then take on this task
        to gather information from external sources and add it to the knowledge base.
        
        The research task will be of type RESEARCH, which distinguishes it from normal tasks and
        evaluation tasks. Research tasks should result in the creation of new knowledge items.
        
        Args:
            ctx: The MCP context containing session information.
            topic: The general topic or subject area that needs research.
            required_skill: The skill required to perform this research. This should be a skill
                           from existing skill domains in the system.
            research_goal: A clear statement of what the research should accomplish.
            details: Optional detailed information about the research requirements, sources to 
                    consult, or specific questions that need to be answered.
            
        Returns:
            A dictionary representation of the newly created research task object.
        """
        from taskhub.services import task_publish
        
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        
        # 构建研究任务的详细信息
        task_details = f"""Research Task: {topic}
        
Goal: {research_goal}

Expected Outcome: Produce a knowledge item that can be added to the knowledge base to help other hunters.

Details: {details or 'No additional details provided.'}

Instructions:
1. Research the topic using reliable external sources
2. Synthesize the information into a coherent knowledge item
3. Add the knowledge item to the system using the knowledge_add tool
4. Include proper citations and sources in the knowledge item"""
        
        # 发布研究任务
        task = await task_publish(
            store, 
            name=f"Research: {topic}", 
            details=task_details, 
            required_skill=required_skill, 
            publisher_id=hunter_id,
            task_type="RESEARCH"  # 明确指定任务类型为研究任务
        )
        
        logger.info(f"Hunter {hunter_id} created research task {task.id} for topic: {topic}")
        return task.model_dump()

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