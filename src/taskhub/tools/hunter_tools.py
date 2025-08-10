"""
Hunter-related tools for the Taskhub system.
"""

import logging
from typing import Any, cast, List
from mcp.server.fastmcp import Context

# Import the FastMCP instance from mcp_server
from .. import mcp

from taskhub.services import (
    hunter_register,
    hunter_study,
    get_hunter
)
from taskhub.context import get_app_context
from ..utils.error_handler import (
    handle_tool_errors, 
    create_success_response,
    ValidationError,
    NotFoundError,
    validate_required_fields,
    validate_string_length
)

logger = logging.getLogger(__name__)

@mcp.tool()
@handle_tool_errors
async def register_yourself(ctx: Context, skills: dict[str, int] | None = None) -> dict[str, Any]:
    """Register yourself as a new hunter with optional initial skills.
    
    This tool registers you as a new hunter in the system with an optional set of initial skills.
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
        ctx: The application context.
        skills: Optional dictionary mapping skill names to initial skill levels (0-100).
               Skill names must be from existing skill domains in the system.
        
    Returns:
        A dictionary representation of the registered hunter object, along with the system guide.
    """
    context = await get_app_context(ctx)
    store = context.store
    hunter_id = context.hunter_id
    
    # Validate skills if provided
    if skills:
        if not isinstance(skills, dict):
            raise ValidationError("skills must be a dictionary", field="skills")
        for skill_name, skill_level in skills.items():
            if not isinstance(skill_name, str):
                raise ValidationError("All skill names must be strings", field="skills")
            validate_string_length(skill_name, 1, 50, "skill name")
            if not isinstance(skill_level, int):
                raise ValidationError("All skill levels must be integers", field="skills")
            if skill_level < 0 or skill_level > 100:
                raise ValidationError("Skill levels must be between 0 and 100", field="skills")
    
    logger.info(f"Registering hunter")
    if skills:
        logger.debug(f"Initial skills: {skills}")
    
    hunter = await hunter_register(store, context.hunter_id, skills)
    
    # 记录猎人注册成功
    logger.info(f"Hunter registered successfully with reputation: {hunter.reputation}")
    
    # 获取系统指南
    from taskhub.services.system_service import get_system_guide
    system_guide = await get_system_guide()
    
    # 返回猎人信息和系统指南
    result = hunter.model_dump()
    result["system_guide"] = system_guide
    
    logger.debug(f"Returning hunter info")
    return create_success_response(result, "Hunter registered successfully")

@mcp.tool()
@handle_tool_errors
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
        ctx: The application context.
        knowledge_id: The unique identifier of the knowledge item to study.
        
    Returns:
        A dictionary representation of the updated hunter object with improved skills.
        
    Raises:
        ValueError: If the hunter or knowledge item is not found.
    """
    context = await get_app_context(ctx)
    store = context.store
    
    # Validate knowledge_id
    validate_required_fields({"knowledge_id": knowledge_id}, ["knowledge_id"])
    validate_string_length(knowledge_id, 1, 100, "knowledge_id")
    
    logger.info(f"Studying knowledge item: {knowledge_id}")
    
    hunter = await hunter_study(store, context.hunter_id, knowledge_id)
    
    logger.info(f"Successfully studied knowledge item {knowledge_id}")
    logger.debug(f"Updated hunter skills: {hunter.skills}")
    
    return create_success_response(hunter.model_dump(), "Knowledge item studied successfully")

