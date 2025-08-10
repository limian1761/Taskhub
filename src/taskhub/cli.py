"""
Taskhub CLI
处理命令行参数并启动相应的服务。
"""

import argparse
import asyncio
import sys
from taskhub.api_server import main as api_main
from taskhub.mcp_server import main as mcp_main

async def unified_main():
    """启动统一服务（API和MCP）"""
    # 使用 asyncio.gather 同时运行 API 和 MCP 服务
    tasks = [api_main(), mcp_main()]
    await asyncio.gather(*tasks)

def main():
    parser = argparse.ArgumentParser(description="Taskhub服务管理器")
    parser.add_argument(
        "service", 
        choices=["api", "mcp", "unified", "all", "cli"], 
        help="要启动的服务: api (仅API服务), mcp (仅MCP服务), unified (统一服务), all (API和MCP服务), cli (CLI模式)"
    )
    parser.add_argument("--host", default="localhost", help="服务绑定的主机地址")
    parser.add_argument("--port", type=int, default=None, help="服务绑定的端口")
    
    # 解析已知参数，忽略未知参数
    args, unknown = parser.parse_known_args()
    
    # 根据选择的服务启动相应的服务
    if args.service == "api":
        # 直接调用api_main，参数通过环境变量或直接传递
        import os
        if args.host != "localhost":
            os.environ["HOST"] = args.host
        if args.port is not None:
            os.environ["PORT"] = str(args.port)
        api_main()
    elif args.service == "mcp":
        # 直接调用mcp_main，参数通过环境变量或直接传递
        import os
        if args.host != "localhost":
            os.environ["HOST"] = args.host
        if args.port is not None:
            os.environ["PORT"] = str(args.port)
        mcp_main()
    elif args.service == "unified":
        # 直接调用unified_main，参数通过环境变量或直接传递
        import os
        if args.host != "localhost":
            os.environ["HOST"] = args.host
        if args.port is not None:
            os.environ["PORT"] = str(args.port)
        unified_main()
    elif args.service == "cli":
        # CLI模式，不启动任何服务
        print("CLI模式已启动。请使用相应的命令与Taskhub交互。")
        # 这里可以添加CLI交互逻辑
        pass
    elif args.service == "all":
        # 启动所有服务
        print("启动所有服务...")
        asyncio.run(unified_main())

if __name__ == "__main__":
    main()