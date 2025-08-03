import logging
import os
import sys
from typing import Literal, cast

import click

# 确保在从包外部运行时，src目录在路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from taskhub.server import app

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--host",
    default=os.getenv("TASKHUB_HOST", "0.0.0.0"),
    help="Host to bind to. Defaults to TASKHUB_HOST env or 0.0.0.0.",
)
@click.option(
    "--port",
    default=int(os.getenv("TASKHUB_PORT", 3000)),
    help="Port to listen on. Defaults to TASKHUB_PORT env or 3000.",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default=os.getenv("TASKHUB_TRANSPORT", "sse"),
    help="Transport type. Defaults to TASKHUB_TRANSPORT env or sse.",
)
def main(host: str, port: int, transport: str):
    """Main entry point for the Taskhub server."""
    logger.info(f"Starting Taskhub server with transport: {transport}")
    if transport != "stdio":
        logger.info(f"Binding to host: {host}, port: {port}")

    try:
        # Update app settings for SSE/HTTP transport
        app.settings.host = host
        app.settings.port = port

        # Run the server with the specified transport
        logger.info("Server starting...")
        # We can safely cast here because click.Choice ensures the value is one of the literals.
        transport_literal = cast(Literal["stdio", "sse", "streamable-http"], transport)
        app.run(transport=transport_literal)
        logger.info("Server started successfully.")
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
