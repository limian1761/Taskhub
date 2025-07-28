#!/bin/bash
# 开发模式启动脚本

# 创建必要的目录
mkdir -p data logs

# 启动开发服务器
echo "Starting Taskhub MCP Server in development mode..."
taskhub --transport sse --host 0.0.0.0 --port 8000