"""
Task-related tools for the Taskhub system.

This module contains tools for managing tasks within the Taskhub system,
including task creation, assignment, progress tracking, and completion.
Tasks are organized within domains, which categorize tasks by skill requirements
and application areas. Users can only work with tasks in domains they have access to.
"""

import logging
from typing import Any, Dict, List, Optional
from mcp.server.fastmcp import Context

# Import the FastMCP instance from mcp_server
from .. import mcp

from taskhub.models.task import TaskStatus
from taskhub.services import (
    task_publish,
    task_claim,
    task_start,
    task_complete,
    task_list,
    get_task,
    report_submit
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
from ..utils.performance_monitor import monitor_performance

logger = logging.getLogger(__name__)

@mcp.tool()
@handle_tool_errors
@monitor_performance("publish_task")
async def publish_task(
    ctx: Context,
    name: str,
    details: str,
    required_skill: str,
    depends_on: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Publish a new task for AI agents to process.
    
    This tool allows a task creator to publish a new task specifically designed for AI agents.
    The task details should be written as prompts that guide the AI agent in completing the task.
    Tasks are processed by AI agents with specific skills, and may depend on other tasks.
    
    When creating tasks for AI agents, consider:
    1. Write clear and specific instructions in the 'details' field
    2. Identify the required skill that AI agents must possess
    3. Specify any dependencies on other tasks
    4. Provide examples or constraints as needed
    
    Note: Tasks are associated with skill domains. In Taskhub, skills and domains are the same
    concept but with different names used in different contexts:
    - "Skill" is used when referring to hunter abilities or task requirements
    - "Domain" is used when referring to knowledge areas or categories
    
    You can only specify skills that already exist in the system. If you need a new 
    skill domain, you must first create it using the domain creation tool.
    
    Args:
        ctx: The application context.
        name: The name/title of the task (should be descriptive for AI agents).
        details: Detailed instructions/prompt for the AI agent. This should be written as a 
                clear prompt that guides the AI agent on what needs to be accomplished.
        required_skill: The skill required for an AI agent to complete this task. Must be 
                       from existing skill domains in the system. In Taskhub, skills and 
                       domains are the same concept.
        depends_on: Optional list of task IDs that must be completed before this task.
        
    Returns:
        A dictionary representation of the newly created task object.
    """
    logger.info(f"Publishing task '{name}' with skill '{required_skill}'")
    context = await get_app_context(ctx)
    store = context.store
    hunter_id = context.hunter_id
    
    task = await task_publish(store, name, details, required_skill, hunter_id, depends_on)
    logger.info(f"Task {task.id} published successfully")
    return task.model_dump()

@mcp.tool()
@handle_tool_errors
@monitor_performance("claim_task")
async def claim_task(ctx: Context, task_id: str) -> Dict[str, Any]:
    """Claim a task for a hunter.
    
    This tool allows a hunter to claim a task, marking it as assigned to them.
    Once claimed, other hunters will not be able to claim the same task.
    
    Args:
        ctx: The application context.
        task_id: The unique identifier of the task to be claimed.
        
    Returns:
        A dictionary representation of the updated task object.
        
    Raises:
        ValueError: If the task is not found or already claimed by another hunter.
    """
    logger.info(f"Claiming task {task_id}")
    context = await get_app_context(ctx)
    store = context.store
    hunter_id = context.hunter_id
    task = await task_claim(store, task_id, hunter_id)
    logger.info(f"Task {task_id} claimed successfully by hunter {hunter_id}")
    return task.model_dump()

@mcp.tool()
@handle_tool_errors
@monitor_performance("start_task")
async def start_task(ctx: Context, task_id: str) -> Dict[str, Any]:
    """Start working on a task.
    
    This tool allows a hunter to mark a claimed task as 'in progress'.
    It updates the task status to indicate active work is being performed.
    
    Args:
        ctx: The application context.
        task_id: The unique identifier of the task to start working on.
        
    Returns:
        A dictionary representation of the updated task object.
        
    Raises:
        ValueError: If the task is not found or not claimed by the current hunter.
    """
    logger.info(f"Starting task {task_id}")
    context = await get_app_context(ctx)
    store = context.store
    hunter_id = context.hunter_id
    task = await task_start(store, task_id, hunter_id)
    logger.info(f"Task {task_id} started successfully by hunter {hunter_id}")
    return task.model_dump()

@mcp.tool()
@handle_tool_errors
@monitor_performance("complete_task")
async def complete_task(ctx: Context, task_id: str, result: str) -> Dict[str, Any]:
    """Complete a task with a result.
    
    This tool allows a hunter to mark a task as completed, providing the result
    of their work. This will trigger the creation of a report for evaluation.
    
    Args:
        ctx: The application context.
        task_id: The unique identifier of the task to complete.
        result: A string describing the result or outcome of the completed task.
        
    Returns:
        A dictionary representation of the updated task object.
        
    Raises:
        ValueError: If the task is not found or not claimed by the current hunter.
    """
    logger.info(f"Completing task {task_id}")
    context = await get_app_context(ctx)
    store = context.store
    hunter_id = context.hunter_id
    task = await task_complete(store, task_id, result, "completed", hunter_id)
    logger.info(f"Task {task_id} completed successfully")
    return task.model_dump()

@mcp.tool()
@handle_tool_errors
@monitor_performance("submit_report")
async def submit_report(
    ctx: Context,
    task_id: str,
    status: str,
    result: Optional[str] = None,
    details: Optional[str] = None,
    auto_score: bool = True,
    update_task_status: bool = True
) -> Dict[str, Any]:
    """Submit a report for a completed task. On success, may trigger an automated
    evaluation task workflow.
    
    Args:
        ctx: The application context.
        task_id: The unique identifier of the task.
        status: The status of the report (e.g., 'completed', 'rejected').
        result: Optional result string describing the outcome.
        details: Optional detailed information about the report.
        auto_score: Whether to automatically score the report (feature flag).
        update_task_status: Whether to update the task status (automation logic).
        
    Returns:
        A dictionary representation of the report object.
    """
    from taskhub.context import get_app_context
    from taskhub.services import hunter_service, task_service
    from taskhub.models.task import TaskType
    from taskhub.utils.config import config
    
    logger.info(f"Submitting report for task {task_id}")
    context = await get_app_context(ctx)
    store = context.store

    
    hunter_id = context.hunter_id
    
    await store.begin()
    try:
        # 1. 提交原始报告
        report = await report_submit(store, task_id, hunter_id, status, result, details)
        
        # 2. 检查特性开关，决定是否执行自动化流程
        if config.get("features.auto_create_evaluation_tasks", True):
            original_task = await store.get_task(task_id)
            
            # 3. 上下文感知触发：仅为高优、非评价任务创建评价任务
            if original_task and original_task.priority > 3 and original_task.type != TaskType.EVALUATION:
                # 4. 智能路由：找到最佳评价者
                best_evaluator = await hunter_service.find_best_hunter_for_task(
                    store,
                    skill=original_task.required_skill,
                    exclude_hunter_ids=[hunter_id]
                )
                
                assignee_id = best_evaluator.id if best_evaluator else None
                
                # 5. 创建并指派评价任务
                eval_task_name = f"Evaluate Report for: {original_task.name}"
                eval_task_details = f"Review report {report.id} for task {original_task.id}."
                
                await task_service.task_publish(
                    store=store,
                    name=eval_task_name,
                    details=eval_task_details,
                    required_skill=original_task.required_skill,
                    publisher_id="system_automata",
                    type=TaskType.EVALUATION,
                    parent_task_id=original_task.id,
                    assignee_id=assignee_id
                )
                logger.info(f"Automated evaluation task created and assigned to {assignee_id}")
        
        await store.commit()
        logger.info(f"Report submitted successfully with ID: {report.id}")
        return report.model_dump()
        
    except Exception as e:
        await store.rollback()
        logger.error(f"Failed to submit report: {str(e)}")
        raise

@mcp.tool()
@handle_tool_errors
@monitor_performance("list_tasks")
async def list_tasks(
    ctx: Context,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """List tasks with optional filtering.
    
    Args:
        ctx: The application context.
        status: Optional task status filter.
        priority: Optional task priority filter.
        assignee_id: Optional assignee ID filter.
        tags: Optional tags filter.
        
    Returns:
        List of task dictionaries.
    """
    context = await get_app_context(ctx)
    store = context.store
    
    # Parse filters
    filters = {}
    if status:
        try:
            filters["status"] = TaskStatus(status)
        except ValueError:
            raise ValidationError(f"Invalid status: {status}", field="status")
    if priority:
        try:
            from taskhub.models.task import TaskPriority
            filters["priority"] = TaskPriority(priority)
        except ValueError:
            raise ValidationError(f"Invalid priority: {priority}", field="priority")
    if assignee_id:
        filters["assignee_id"] = assignee_id
    if tags:
        if not isinstance(tags, list):
            raise ValidationError("tags must be a list", field="tags")
        filters["tags"] = tags
    
    tasks = await task_list(store, **filters)
    return create_success_response([task.model_dump() for task in tasks])

@mcp.tool()
@handle_tool_errors
@monitor_performance("get_task")
async def get_task(ctx: Context, task_id: str) -> Dict[str, Any]:
    """Get a specific task by ID.
    
    Args:
        ctx: The application context.
        task_id: The task ID to retrieve.
        
    Returns:
        Task dictionary.
    """
    context = await get_app_context(ctx)
    store = context.store
    task = await get_task(store, task_id)
    
    if not task:
        raise NotFoundError(f"Task {task_id} not found")
    
    return create_success_response(task.model_dump())

@mcp.tool()
@handle_tool_errors
@monitor_performance("update_task")
async def update_task(
    ctx: Context,
    task_id: str,
    name: Optional[str] = None,
    details: Optional[str] = None,
    priority: Optional[int] = None,
    status: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Update a task's properties.
    
    Args:
        ctx: The application context.
        task_id: The task ID to update.
        name: Optional new name.
        details: Optional new details.
        priority: Optional new priority.
        status: Optional new status.
        tags: Optional new tags.
        
    Returns:
        Updated task dictionary.
    """
    context = await get_app_context(ctx)
    store = context.store
    
    # 获取现有任务
    task = await get_task(store, task_id)
    if not task:
        raise NotFoundError(f"Task {task_id} not found")
    
    # 更新字段
    if name is not None:
        task.name = name
    if details is not None:
        task.details = details
    if priority is not None:
        task.priority = priority
    if status is not None:
        try:
            task.status = TaskStatus(status)
        except ValueError:
            raise ValidationError(f"Invalid status: {status}", field="status")
    if tags is not None:
        task.tags = tags
    
    # 保存更新
    updated_task = await store.update_task(task)
    return create_success_response(updated_task.model_dump())

