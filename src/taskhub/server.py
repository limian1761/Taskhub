import json
import logging
import logging.config
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from mcp.server.fastmcp import Context, FastMCP
from mcp.shared.context import RequestContext
from pydantic import Field

import taskhub.services as taskhub_api
from taskhub.models.task import TaskStatus
from taskhub.storage.sqlite_store import SQLiteStore

# --- Logging Setup ---
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

try:
    with open("configs/logging.json") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)

# 创建专门的请求日志记录器
request_logger = logging.getLogger("taskhub.request")

# 从请求头中获取 namespace，不区分大小写
namespace = "default"
hunter_id = "unknown"

if ctx.request:
    # 获取所有请求头并转换为小写键名以便不区分大小写匹配
    headers = {k.lower(): v for k, v in ctx.request.headers.items()}
    
    # 从 TASKHUB_NAMESPACE 头部获取 namespace，不区分大小写
    namespace = headers.get("taskhub_namespace", "default")
    
    # 从 hunter_id 头部获取 hunter_id，不区分大小写
    hunter_id = headers.get("hunter_id", "unknown")

# 将 hunter_id 存储在上下文中供后续使用
ctx.session.namespace = namespace
ctx.session.hunter_id = hunter_id

# --- Application Setup ---
@dataclass
class TaskhubAppContext:
    stores: dict[str, SQLiteStore] = field(default_factory=dict)

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[TaskhubAppContext]:
    logger.info("Initializing Taskhub application")
    ctx = TaskhubAppContext()
    try:
        yield ctx
    finally:
        logger.info("Shutting down Taskhub application")
        for namespace, store in ctx.stores.items():
            logger.info(f"Closing database store for namespace '{namespace}'")
            await store.close()

app = FastMCP("Taskhub", lifespan=app_lifespan)

def get_store(ctx: RequestContext[Any, TaskhubAppContext, Any]) -> SQLiteStore:
    """Get the database store for the current request's namespace."""
    # 从请求头中获取 namespace，不区分大小写
    namespace = "default"
    hunter_id = "unknown"
    
    if ctx.request:
        # 获取所有请求头并转换为小写键名以便不区分大小写匹配
        headers = {k.lower(): v for k, v in ctx.request.headers.items()}
        
        # 从 TASKHUB_NAMESPACE 头部获取 namespace，不区分大小写
        namespace = headers.get("taskhub_namespace", "default")
        
        # 从 hunter_id 头部获取 hunter_id，不区分大小写
        hunter_id = headers.get("hunter_id", "unknown")
    
    # 将 hunter_id 存储在上下文中供后续使用
    ctx.session.namespace = namespace
    ctx.session.hunter_id = hunter_id
    
    # 记录请求信息到请求日志
    if ctx.request:
        request_info = {
            "method": ctx.request.method,
            "url": str(ctx.request.url),
            "namespace": namespace,
            "hunter_id": hunter_id,
        }
        request_logger.info(f"Request context: {request_info}")
    
    app_ctx = ctx.lifespan_context
    if namespace not in app_ctx.stores:
        db_path = f"data/taskhub_{namespace}.db"
        logger.info(f"Creating new database store for namespace '{namespace}' at {db_path}")
        app_ctx.stores[namespace] = SQLiteStore(db_path)
    else:
        logger.debug(f"Reusing existing database store for namespace '{namespace}'")
    return app_ctx.stores[namespace]

# --- Tool Definitions ---

@app.tool("taskhub.task.publish")
async def publish_task(
    ctx: Context,
    name: str,
    details: str,
    required_skill: str,
    created_by: str,
    depends_on: list[str] | None = None,
) -> dict[str, Any]:
    store = get_store(cast(RequestContext, ctx.request_context))
    task = await taskhub_api.task_publish(store, name, details, required_skill, created_by, depends_on)
    return task.model_dump()


@app.tool@app.tool("taskhub.task.claim")
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
    task = await taskhub_api.task_claim(store, task_id, hunter_id)
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
    task = await taskhub_api.task_start(store, task_id, hunter_id)
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
    task = await taskhub_api.task_complete(store, task_id, result, "completed", hunter_id)
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
    report = await taskhub_api.report_submit(store, task_id, hunter_id, status, result, details)
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
    tasks = await taskhub_api.task_list(store, status, required_skill, assignee)
    return [task.model_dump() for task in tasks]

@app.tool("taskhub.hunter.register")
async def register_hunter(ctx: Context, skills: dict[str, int] | None = None) -> dict[str, Any]:
    """Register a new hunter with optional initial skills.
    
    This tool registers a new hunter in the system with an optional set of initial skills.
    If the hunter already exists, it will update their skills. This is typically called
    when a hunter first connects to the system.
    
    Args:
        ctx: The MCP context containing session information.
        skills: Optional dictionary mapping skill names to initial skill levels (0-100).
        
    Returns:
        A dictionary representation of the registered hunter object.
    """
    store = get_store(cast(RequestContext, ctx.request_context))
    hunter_id = ctx.session.agent_id
    hunter = await taskhub_api.hunter_register(store, hunter_id, skills)
    return hunter.model_dump()

@app.tool("taskhub.hunter.study")
async def hunter_study(ctx: Context, knowledge_id: str) -> dict[str, Any]:
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
    hunter_id = ctx.session.agent_id
    hunter = await taskhub_api.hunter_study(store, hunter_id, knowledge_id)
    return hunter.model_dump()

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
    knowledge_item = await taskhub_api.knowledge_add(store, title, content, source, skill_tags, created_by)
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
    items = await taskhub_api.knowledge_list(store, skill_tag)
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
    items = await taskhub_api.knowledge_search(store, query, limit)
    return [item.model_dump() for item in items]

@app.tool("taskhub.system.get_guide")
async def get_system_guide(ctx: Context) -> str:
    """Retrieve the system guide for hunters.
    
    This tool provides hunters with a comprehensive guide to using the Taskhub system,
    including information about available tools, workflow processes, and best practices.
    
    Args:
        ctx: The MCP context containing session information.
        
    Returns:
        A string containing the complete system guide.
    """
    await ctx.info("Hunter requested the system guide.")
    return await taskhub_api.get_system_guide()

# --- Resource Definitions ---
# (Resource definitions remain unchanged for now, but should be updated
# in the future to align with the new 'skill' based model)
@app.resource("task://{task_id}")
async def get_task_resource(ctx: Context, task_id: str) -> dict[str, Any]:
    """Get task resource by ID.
    
    Args:
        ctx: The MCP context containing session information.
        task_id: The unique identifier of the task.
        
    Returns:
        A dictionary representation of the task object.
    """
    store = get_store(cast(RequestContext, ctx.request_context))
    task = await taskhub_api.get_task(store, task_id)
    if task is None:
        raise ValueError(f"Task with ID {task_id} not found")
    return task.model_dump()

@app.resource("hunter://{hunter_id}")
async def get_hunter_resource(ctx: Context, hunter_id: str) -> dict[str, Any]:
    """Get hunter resource by ID.
    
    Args:
        ctx: The MCP context containing session information.
        hunter_id: The unique identifier of the hunter.
        
    Returns:
        A dictionary representation of the hunter object.
    """
    store = get_store(cast(RequestContext, ctx.request_context))
    hunter = await taskhub_api.get_hunter(store, hunter_id)
    if hunter is None:
        raise ValueError(f"Hunter with ID {hunter_id} not found")
    return hunter.model_dump()

@app.resource("agent://{agent_id}")
async def get_agent_resource(ctx: Context, agent_id: str) -> dict[str, Any]:
    """Get agent resource by ID.
    
    Args:
        ctx: The MCP context containing session information.
        agent_id: The unique identifier of the agent.
        
    Returns:
        A dictionary representation of the agent object.
    """
    # For now, we treat agents the same as hunters in this implementation
    store = get_store(cast(RequestContext, ctx.request_context))
    hunter = await taskhub_api.get_hunter(store, agent_id)
    if hunter is None:
        raise ValueError(f"Agent/Hunter with ID {agent_id} not found")
    return hunter.model_dump()
