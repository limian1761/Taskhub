import json
import logging
import logging.config
from pathlib import Path

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from mcp.server.fastmcp import FastMCP

# Import our modularized components
from taskhub.context import (
    TaskhubAppContext,
    app_lifespan,
    get_store
)
from taskhub.tools.hunter_tools import register_hunter_tools
from taskhub.tools.knowledge_tools import register_knowledge_tools
from taskhub.tools.task_tools import register_task_tools
from taskhub.tools.discussion_tools import register_discussion_tools
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.services import system_service
from taskhub.utils.config import config

logger = logging.getLogger(__name__)

# --- Logging Setup ---
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

try:
    with open("configs/logging.json") as f:
        log_config = json.load(f)
        logging.config.dictConfig(log_config)
except Exception:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# 创建一个全局的调度器实例
scheduler = AsyncIOScheduler()

async def run_stale_task_check():
    """Scheduler job wrapper to create a store instance and run the check."""
    # 注意：调度器作业是独立运行的，需要自己的store实例
    # 这里我们假设默认的namespace是'default'，在多租户场景下可能需要更复杂的处理
    db_path = config.get_database_path(config.get_default_namespace())
    store = SQLiteStore(db_path)
    await store.connect()
    try:
        await system_service.check_and_escalate_stale_tasks(store)
    finally:
        await store.close()

# 创建专门的请求日志记录器
request_logger = logging.getLogger("taskhub.request")

# --- Application Setup ---
app = FastMCP("Taskhub", lifespan=app_lifespan)

# Register all tools
register_task_tools(app)
register_hunter_tools(app)
register_knowledge_tools(app)

# --- Tool Definitions ---
# All tool definitions have been moved to modular tool files


def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""
    app = FastMCP("Taskhub")
    
    # 注册所有工具
    register_hunter_tools(app)
    register_knowledge_tools(app)
    register_task_tools(app)
    register_discussion_tools(app)
    
    logger.info("All tools registered successfully")
    return app


def main():
    import argparse
    import asyncio

    parser = argparse.ArgumentParser(description="Taskhub MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="sse",
        help="Transport to use (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (for HTTP transports)")
    parser.add_argument("--port", type=int, default=3000, help="Port to bind to (for HTTP transports)")

    args = parser.parse_args()
    
    # 添加调度作业，每小时运行一次
    scheduler.add_job(run_stale_task_check, 'interval', hours=1)
    
    # 启动调度器
    scheduler.start()

    try:
        if args.transport == "stdio":
            asyncio.run(app.stdio())
        elif args.transport == "sse":
            asyncio.run(app.sse(host=args.host, port=args.port))
        elif args.transport == "streamable-http":
            asyncio.run(app.streamable_http(host=args.host, port=args.port))
        else:
            raise ValueError(f"Unknown transport: {args.transport}")
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()


if __name__ == "__main__":
    main()