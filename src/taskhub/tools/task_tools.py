"""
Task-related tools for the Taskhub system.
"""

import logging
from typing import Any, cast

from mcp.server.fastmcp import Context
from mcp.shared.context import RequestContext
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
from taskhub.context import get_store

logger = logging.getLogger(__name__)


def register_task_tools(app):
    """Register all task-related tools with the FastMCP app."""
    
    @app.tool("taskhub.task.publish")
    async def publish_task(
        ctx: Context,
        name: str,
        details: str,
        required_skill: str,
        created_by: str,
        depends_on: list[str] | None = None,
    ) -> dict[str, Any]:
        """Publish a new task for AI agents to process.
        
        This tool allows a task creator to publish a new task specifically designed for AI agents.
        The task details should be written as prompts that guide the AI agent in completing the task.
        Tasks are processed by AI agents with specific skills, and may depend on other tasks.
        
        When creating tasks for AI agents, consider:
        1. Write clear and specific instructions in the 'details' field
        2. Identify the required skill that AI agents must possess
        3. Specify any dependencies on other tasks
        4. Provide examples or constraints as needed
        
        Args:
            ctx: The MCP context containing session information.
            name: The name/title of the task (should be descriptive for AI agents).
            details: Detailed instructions/prompt for the AI agent. This should be written as a 
                    clear prompt that guides the AI agent on what needs to be accomplished.
            required_skill: The skill required for an AI agent to complete this task.
            created_by: The identifier of the entity that created this task.
            depends_on: Optional list of task IDs that must be completed before this task.
            
        Returns:
            A dictionary representation of the newly created task object.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        task = await task_publish(store, name, details, required_skill, created_by, depends_on)
        return task.model_dump()

    @app.tool("taskhub.task.claim")
    async def claim_task(ctx: Context, task_id: str) -> dict[str, Any]:
        """Claim a task for a hunter.
        
        This tool allows a hunter to claim a task, marking it as assigned to them.
        Once claimed, other hunters will not be able to claim the same task.
        
        Args:
            ctx: The MCP context containing session information.
            task_id: The unique identifier of the task to be claimed.
            
        Returns:
            A dictionary representation of the updated task object.
            
        Raises:
            ValueError: If the task is not found or already claimed by another hunter.
        """
        logger.info(f"Hunter claiming task {task_id}")
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        task = await task_claim(store, task_id, hunter_id)
        logger.info(f"Task {task_id} claimed successfully by hunter {hunter_id}")
        return task.model_dump()

    @app.tool("taskhub.task.start")
    async def start_task(ctx: Context, task_id: str) -> dict[str, Any]:
        """Start working on a task.
        
        This tool allows a hunter to mark a claimed task as 'in progress'.
        It updates the task status to indicate active work is being performed.
        
        Args:
            ctx: The MCP context containing session information.
            task_id: The unique identifier of the task to start working on.
            
        Returns:
            A dictionary representation of the updated task object.
            
        Raises:
            ValueError: If the task is not found or not claimed by the current hunter.
        """
        logger.info(f"Hunter starting task {task_id}")
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        task = await task_start(store, task_id, hunter_id)
        logger.info(f"Task {task_id} started successfully by hunter {hunter_id}")
        return task.model_dump()

    @app.tool("taskhub.task.complete")
    async def complete_task(ctx: Context, task_id: str, result: str) -> dict[str, Any]:
        """Complete a task with a result.
        
        This tool allows a hunter to mark a task as completed, providing the result
        of their work. This will trigger the creation of a report for evaluation.
        
        Args:
            ctx: The MCP context containing session information.
            task_id: The unique identifier of the task to complete.
            result: A string describing the result or outcome of the completed task.
            
        Returns:
            A dictionary representation of the updated task object.
            
        Raises:
            ValueError: If the task is not found or not claimed by the current hunter.
        """
        logger.info(f"Completing task {task_id}")
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        task = await task_complete(store, task_id, result, "completed", hunter_id)
        logger.info(f"Task {task_id} completed successfully")
        return task.model_dump()

    @app.tool("taskhub.report.submit")
    async def submit_report(
        ctx: Context, task_id: str, status: str, result: str | None = None, details: str | None = None
    ) -> dict[str, Any]:
        """Submit a report for a completed task."""
        logger.info(f"Submitting report for task {task_id}")
        store = get_store(cast(RequestContext, ctx.request_context))
        hunter_id = ctx.session.hunter_id
        report = await report_submit(store, task_id, hunter_id, status, result, details)
        logger.info(f"Report submitted successfully with ID: {report.id}")
        return report.model_dump()

    @app.tool("taskhub.task.list")
    async def list_tasks(
        ctx: Context, status: TaskStatus | None = None, required_skill: str | None = None, assignee: str | None = None
    ) -> list[dict[str, Any]]:
        """List tasks with optional filtering.
        
        This tool retrieves a list of tasks, optionally filtered by status, required skill,
        or assignee. This is useful for hunters to find available tasks or for administrators
        to monitor task progress.
        
        Args:
            ctx: The MCP context containing session information.
            status: Optional filter for task status (e.g., PENDING, CLAIMED, IN_PROGRESS, COMPLETED).
            required_skill: Optional filter for tasks requiring a specific skill.
            assignee: Optional filter for tasks assigned to a specific hunter.
            
        Returns:
            A list of dictionary representations of task objects matching the filters.
        """
        store = get_store(cast(RequestContext, ctx.request_context))
        tasks = await task_list(store, status, required_skill, assignee)
        return [task.model_dump() for task in tasks]

    @app.resource("task://{task_id}")
    async def get_task_resource(task_id: str) -> dict[str, Any]:
        """Get task resource by ID.
        
        Args:
            task_id: The unique identifier of the task.
            
        Returns:
            A dictionary representation of the task object.
        """
        # 由于资源函数不能直接访问上下文，我们需要使用全局应用实例来获取存储
        # 这是一个简化实现，实际项目中可能需要更好的解决方案
        from taskhub.server import app
        store = app.state.stores.get("default")  # 获取默认存储实例
        if not store:
            # 如果默认存储不存在，创建一个新的
            from taskhub.storage.sqlite_store import SQLiteStore
            store = SQLiteStore("data/taskhub_default.db")
            await store.connect()
            app.state.stores["default"] = store
            
        task = await get_task(store, task_id)
        if task is None:
            raise ValueError(f"Task with ID {task_id} not found")
        return task.model_dump()
