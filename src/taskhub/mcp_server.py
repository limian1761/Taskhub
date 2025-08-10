"""
Taskhub MCP Server
提供MCP工具服务，处理AI代理的工具调用。
"""

from ast import Import
import json
import logging
import logging.config
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager
from typing import Any, Optional

# Import our modularized components
from taskhub.utils.scheduler_utils import run_stale_task_check
from taskhub.context import taskhub_lifespan

# Import the global MCP instance
# Import the FastMCP instance from mcp_server
from . import mcp


# Import tools to register them
import taskhub.tools.task_tools
import taskhub.tools.hunter_tools
import taskhub.tools.knowledge_tools
import taskhub.tools.discussion_tools
import taskhub.tools.system_prompts

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

# Namespace and hunter ID will be managed through context variables
# The context system handles namespace and hunter ID automatically


# --- Main Execution ---
def main(host="localhost", port=8000):
    """
    主MCP服务器入口点

    Args:
        host (str): Host to bind to
        port (int): Port to bind to
    """
    from taskhub.utils.welcome import print_welcome_banner
    import os

    # clear the console
    _ = os.system('cls' if os.name == 'nt' else 'clear')

    print_welcome_banner()

    # 如果通过环境变量提供了参数，则使用环境变量的值
    host = os.environ.get("HOST", host)
    port = int(os.environ.get("PORT", port))

    logger.info(f"Starting Taskhub MCP Server on http://{host}:{port}")
    mcp.settings.host = host
    mcp.settings.port = port

    mcp.run("sse")

if __name__ == "__main__":
    main()