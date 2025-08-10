"""
Discussion-related tools for the Taskhub system.
"""
import logging
from typing import Any
from mcp.server.fastmcp import Context

# Import the FastMCP instance from mcp_server
from .. import mcp

from taskhub.services import discussion_service
from taskhub.context import get_app_context
logger = logging.getLogger(__name__)

# Define the tool functions
@mcp.tool()
async def post_discussion_message(ctx: Context, message: str) -> dict[str, Any]:
    """
    Posts a message to the public discussion forum.

    This tool allows a hunter to communicate with all other hunters. It will first
    retrieve any unread messages for the hunter. If there are no unread messages,
    it will automatically prepend a summary of the hunter's recent work to the message.

    Args:
        ctx: The application context.
        message: The message content to post.

    Returns:
        A dictionary containing a list of unread messages and a status confirmation.
    """
    context = await get_app_context(ctx)
    store = context.store

    # 1. Get unread messages
    unread_messages = await discussion_service.get_unread_messages(store)

    # 2. Mark messages as read
    await discussion_service.mark_as_read(store)

    # 3. Prepare the final message content
    final_content = message
    if not unread_messages:
        # Get recent tasks for the hunter
        recent_tasks = await store.list_tasks(status="completed")
        if not recent_tasks:
            recent_tasks = await store.list_tasks(status="in_progress")

        if recent_tasks:
            task_names = [t.name for t in recent_tasks[:3]]
            work_summary = f"My recent work includes: {', '.join(task_names)}. "
            final_content = work_summary + message

    # 4. Post the final message
    await discussion_service.post_message(store, final_content)

    return {
        "unread_messages": [msg.model_dump() for msg in unread_messages],
        "status": "Message posted successfully.",
    }

