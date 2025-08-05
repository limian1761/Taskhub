import json
import logging
import logging.config
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Import our modularized components
from taskhub.context import (
    TaskhubAppContext,
    app_lifespan,
    get_store
)
from taskhub.tools.task_tools import register_task_tools
from taskhub.tools.hunter_tools import register_hunter_tools
from taskhub.tools.knowledge_tools import register_knowledge_tools

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

# --- Application Setup ---
app = FastMCP("Taskhub", lifespan=app_lifespan)

# Register all tools
register_task_tools(app)
register_hunter_tools(app)
register_knowledge_tools(app)

# --- Tool Definitions ---
# All tool definitions have been moved to modular tool files

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

    if args.transport == "stdio":
        asyncio.run(app.stdio())
    elif args.transport == "sse":
        asyncio.run(app.sse(host=args.host, port=args.port))
    elif args.transport == "streamable-http":
        asyncio.run(app.streamable_http(host=args.host, port=args.port))
    else:
        raise ValueError(f"Unknown transport: {args.transport}")


if __name__ == "__main__":
    main()
