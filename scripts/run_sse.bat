@echo off
REM SSE模式启动脚本

if not exist "data" mkdir data

echo Starting Taskhub MCP Server with SSE transport...
taskhub --transport sse