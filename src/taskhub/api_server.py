"""
Taskhub API Server
提供RESTful API服务，处理任务、猎人、知识等业务逻辑。
"""

import json
import logging
import logging.config
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any, List

from fastapi import FastAPI, Depends,  Query, Request, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
from datetime import datetime

# Import our modularized components
from taskhub.utils.scheduler_utils import run_stale_task_check
from taskhub.storage.sqlite_store import SQLiteStore

# Import service modules and functions
from taskhub.services import (
    system_service,
    task_service,
    hunter_service,
    knowledge_service,
    report_service,
    discussion_service
)

# Configure logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

try:
    with open("configs/logging.json") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

logger = logging.getLogger(__name__)

# Initialize templates
templates = Jinja2Templates(directory="src/taskhub/templates")

# --- Pydantic Models ---
class DiscussionPostRequest(BaseModel):
    hunter_id: str
    content: str

# --- Dependency ---
async def get_store(namespace: str = Query("default", description="The namespace for the database.")):
    db_path = f"data/{namespace}.db"
    store = SQLiteStore(db_path)
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

# --- Lifespan Management ---
@asynccontextmanager
async def lifespan(app: Any): # Changed to Any to be compatible with Starlette
    logger.info("Taskhub API服务器启动...")
    # 注意：这里移除了任务检查调度器，因为MCP服务器会处理
    yield
    logger.info("Taskhub API服务器关闭...")

# --- App Initialization ---
app = FastAPI(title="Taskhub API", lifespan=lifespan)

# --- API Routers ---
api_router = APIRouter()
system_router = APIRouter(prefix="/api/system", tags=["System"])
task_router = APIRouter(prefix="/api/tasks", tags=["Tasks"])
hunter_router = APIRouter(prefix="/api/hunters", tags=["Hunters"])
knowledge_router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])
report_router = APIRouter(prefix="/api/reports", tags=["Reports"])
discussion_router = APIRouter(prefix="/api/discussion", tags=["Discussion"])
logs_router = APIRouter(prefix="/api/logs", tags=["Logs"])

# --- Route Definitions ---
# Root
@api_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})

# Health Check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "taskhub-api"}

# System Routes
@system_router.get("/task-graph", response_model=Any)
async def get_task_graph_endpoint(store: SQLiteStore = Depends(get_store)):
    return await system_service.get_task_interaction_graph(store)

@system_router.get("/stats", response_model=Any)
async def get_system_stats_endpoint(store: SQLiteStore = Depends(get_store)):
    return await system_service.get_system_stats(store)

@system_router.get("/tasks", response_model=Any)
async def get_all_tasks_endpoint(store: SQLiteStore = Depends(get_store)):
    return await system_service.get_all_tasks(store)

@system_router.get("/namespaces", response_model=List[str])
async def list_namespaces():
    data_dir = Path("data")
    if not data_dir.exists(): return []
    return [f.stem for f in data_dir.glob("*.db")]

# Task Routes (示例，需要补充完整)
@task_router.get("/")
async def list_tasks(store: SQLiteStore = Depends(get_store)):
    return await task_service.list_tasks(store)

@task_router.post("/")
async def create_task(task_data: dict, store: SQLiteStore = Depends(get_store)):
    return await task_service.create_task(store, task_data)

@task_router.get("/{task_id}")
async def get_task(task_id: str, store: SQLiteStore = Depends(get_store)):
    return await task_service.get_task(store, task_id)

@task_router.put("/{task_id}")
async def update_task(task_id: str, task_data: dict, store: SQLiteStore = Depends(get_store)):
    return await task_service.update_task(store, task_id, task_data)

@task_router.delete("/{task_id}")
async def delete_task(task_id: str, store: SQLiteStore = Depends(get_store)):
    return await task_service.delete_task(store, task_id)

# Hunter Routes (示例，需要补充完整)
@hunter_router.get("/")
async def list_hunters(store: SQLiteStore = Depends(get_store)):
    return await hunter_service.list_hunters(store)

@hunter_router.post("/")
async def create_hunter(hunter_data: dict, store: SQLiteStore = Depends(get_store)):
    return await hunter_service.create_hunter(store, hunter_data)

# Knowledge Routes (示例，需要补充完整)
@knowledge_router.get("/")
async def list_knowledge(store: SQLiteStore = Depends(get_store)):
    return await knowledge_service.list_knowledge(store)

# Discussion Routes (示例，需要补充完整)
@discussion_router.post("/post")
async def post_discussion_message(request: DiscussionPostRequest, store: SQLiteStore = Depends(get_store)):
    # 这里需要实现具体的讨论消息发布逻辑
    return {"status": "success", "message": "Message posted"}

# Report Routes (示例，需要补充完整)
@report_router.get("/")
async def list_reports(store: SQLiteStore = Depends(get_store)):
    return await report_service.list_reports(store)

# --- Include Routers ---
app.include_router(api_router)
app.include_router(system_router)
app.include_router(task_router)
app.include_router(hunter_router)
app.include_router(knowledge_router)
app.include_router(report_router)
app.include_router(discussion_router)
app.include_router(logs_router)

# --- Main Execution ---
def main(host="localhost", port=8001, dev=False):
    """
    主API服务器入口点
    
    Args:
        host (str): Host to bind to
        port (int): Port to bind to
        dev (bool): Enable development mode (auto-reload)
    """
    from taskhub.utils.welcome import print_welcome_banner
    import os
    
    print_welcome_banner()

    # 如果通过环境变量提供了参数，则使用环境变量的值
    host = os.environ.get("HOST", host)
    port = int(os.environ.get("PORT", port))
    dev = os.environ.get("DEV", "false").lower() == "true" or dev
    
    logger.info(f"Starting Taskhub API Server on http://{host}:{port}")
    uvicorn.run(
        "taskhub.api_server:app",
        host=host,
        port=port,
        reload=dev,
        log_level="info"
    )

if __name__ == "__main__":
    main()