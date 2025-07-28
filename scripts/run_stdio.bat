@echo off
REM stdio模式启动脚本

if not exist "data" mkdir data

echo Starting Taskhub MCP Server with stdio transport...
taskhub --transport stdio