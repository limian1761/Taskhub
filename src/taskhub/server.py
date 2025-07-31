# ... (imports) ...
from taskhub.models.task import Task, TaskListParams
from taskhub.models.report import Report, ReportListParams
from fastapi import Depends

# ... (lifespan) ...

mcp = FastMCP("taskhub", lifespan=app_lifespan)

# --- Resources ---
@mcp.resource("task://")
async def list_tasks(ctx: Context, params: TaskListParams = Depends()) -> List[Task]:
    db = ctx.request_context.lifespan_context.db
    return await taskhub_api.list_tasks(db, **params.model_dump())

@mcp.resource("report://")
async def list_reports(ctx: Context, params: ReportListParams = Depends()) -> List[Report]:
    db = ctx.request_context.lifespan_context.db
    return await taskhub_api.list_reports(db, **params.model_dump())

# ... (rest of the file) ...
