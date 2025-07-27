import sys
import asyncio
from pathlib import Path
import argparse

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.types import Tool
import mcp.types as types

from .tools.taskhub import task_list, task_claim, report_submit, task_publish, task_delete, report_evaluate, task_archive, task_suggest_agents, agent_register
from .utils.config import config

# 创建MCP服务器实例
server = Server("taskhub")

# 注册所有工具
@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [
        Tool(
            name="task_list",
            description="列出所有任务，支持按状态、能力、分配者过滤",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "任务状态 (pending, claimed, completed, failed)",
                        "enum": ["pending", "claimed", "completed", "failed"]
                    },
                    "capability": {
                        "type": "string",
                        "description": "所需能力"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "分配代理ID"
                    }
                }
            }
        ),
        Tool(
            name="task_publish",
            description="发布新任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "任务名称"
                    },
                    "details": {
                        "type": "string",
                        "description": "任务详情"
                    },
                    "capability": {
                        "type": "string",
                        "description": "所需能力"
                    },
                    "depends_on": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "依赖任务ID列表"
                    }
                },
                "required": ["name", "details", "capability"]
            }
        ),
        Tool(
            name="task_claim",
            description="代理认领任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务ID"
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "代理ID"
                    }
                },
                "required": ["task_id", "agent_id"]
            }
        ),
        Tool(
            name="report_submit",
            description="提交任务报告，将任务执行结果和状态更新到报告数据库",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "任务ID"
                    },
                    "status": {
                        "type": "string",
                        "description": "任务执行状态 (completed, failed)",
                        "enum": ["completed", "failed"]
                    },
                    "details": {
                        "type": "string",
                        "description": "任务执行过程的详细描述"
                    },
                    "result": {
                        "type": "string",
                        "description": "任务执行结果"
                    }
                },
                "required": ["task_id", "status", "result"]
            }
        ),
        Tool(
            name="task_delete",
            description="删除任务",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "要删除的任务ID"
                    },
                    "force": {
                        "type": "boolean",
                        "description": "是否强制删除，即使有依赖关系",
                        "default": False
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="report_evaluate",
            description="报告评价",
            inputSchema={
                "type": "object",
                "properties": {
                    "report_id": {
                        "type": "string",
                        "description": "要评价的报告ID"
                    },
                    "score": {
                        "type": "number",
                        "description": "评价分数 (0-100)"
                    },
                    "reputation_change": {
                        "type": "number",
                        "description": "声望值变化"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "评价反馈"
                    },
                    "capability_updates": {
                        "type": "object",
                        "description": "能力等级更新",
                        "additionalProperties": {"type": "integer"}
                    }
                },
                "required": ["report_id", "score", "reputation_change", "feedback"]
            }
        ),
        Tool(
            name="task_archive",
            description="任务归档",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "要归档的任务ID"
                    }
                },
                "required": ["task_id"]
            }
        ),
        Tool(
            name="task_suggest_agents",
            description="为代理推荐最匹配的任务，基于能力和声望排序",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "代理ID"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量限制",
                        "default": 10
                    }
                },
                "required": ["agent_id"]
            }
        ),
        Tool(
            name="agent_register",
            description="代理注册功能，用于代理首次进入时声明其能力",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "代理的唯一标识符"
                    },
                    "name": {
                        "type": "string",
                        "description": "代理的显示名称"
                    },
                    "capabilities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "代理具备的能力列表"
                    },
                    "capability_levels": {
                        "type": "object",
                        "description": "各项能力的等级 (1-10)",
                        "additionalProperties": {"type": "integer"}
                    }
                },
                "required": ["agent_id", "name", "capabilities", "capability_levels"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    try:
        if name == "task_list":
            from .tools.taskhub import TaskListParams
            params = TaskListParams(**arguments)
            result = await task_list(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "task_publish":
            from .tools.taskhub import TaskPublishParams
            params = TaskPublishParams(**arguments)
            result = await task_publish(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "task_claim":
            from .tools.taskhub import TaskClaimParams
            params = TaskClaimParams(**arguments)
            result = await task_claim(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "report_submit":
            from .tools.taskhub import ReportSubmitParams
            params = ReportSubmitParams(**arguments)
            result = await report_submit(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "task_delete":
            from .tools.taskhub import TaskDeleteParams
            params = TaskDeleteParams(**arguments)
            result = await task_delete(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "report_evaluate":
            from .tools.taskhub import ReportEvaluateParams
            params = ReportEvaluateParams(**arguments)
            result = await report_evaluate(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "task_archive":
            from .tools.taskhub import TaskArchiveParams
            params = TaskArchiveParams(**arguments)
            result = await task_archive(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "task_suggest_agents":
            from .tools.taskhub import TaskSuggestParams
            params = TaskSuggestParams(**arguments)
            result = await task_suggest_agents(params)
            return [types.TextContent(type="text", text=str(result))]
        elif name == "agent_register":
            from .tools.taskhub import AgentRegisterParams
            params = AgentRegisterParams(**arguments)
            result = await agent_register(params)
            return [types.TextContent(type="text", text=str(result))]
        else:
            raise ValueError(f"Unknown tool: {name}")
    except Exception as e:
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    parser = argparse.ArgumentParser(description='Taskhub MCP Server - 任务管理和代理协调服务器')
    parser.add_argument(
        '--transport', 
        choices=['stdio', 'sse'], 
        default=config.get('server.transport', 'stdio'),
        help='传输方式 (default: stdio)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=config.get('server.port', 8000),
        help='SSE模式下的端口 (default: 8000)'
    )
    parser.add_argument(
        '--host', 
        default=config.get('server.host', 'localhost'),
        help='SSE模式下的主机地址 (default: localhost)'
    )
    
    args = parser.parse_args()
    
    if args.transport == 'sse':
        try:
            from mcp.server.fastapi import serve_app
            print(f"Starting Taskhub MCP Server with SSE transport on {args.host}:{args.port}")
            await serve_app(server, host=args.host, port=args.port)
        except ImportError:
            print("Warning: FastAPI not available, falling back to stdio transport")
            from mcp.server.stdio import stdio_server
            print("Starting Taskhub MCP Server with stdio transport")
            async with stdio_server() as (read_stream, write_stream):
                await server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="taskhub",
                        server_version="2.0.0",
                        capabilities=server.get_capabilities()
                    )
                )
    else:
        from mcp.server.stdio import stdio_server
        print("Starting Taskhub MCP Server with stdio transport")
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="taskhub",
                    server_version="2.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

if __name__ == "__main__":
    asyncio.run(main())