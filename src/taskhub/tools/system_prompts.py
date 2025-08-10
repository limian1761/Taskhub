"""
System-level prompts for the Taskhub MCP server.
"""

from .. import mcp
@mcp.prompt(title="Start Task")
def start_task() -> str:
    """
    Returns the main operating guide for Taskhub hunters.

    This guide explains the core concepts, rules, and workflows of the system,
    teaching the hunter how to be effective.
    """
    return "please regist yourself first and then check the system_guide file"
