@echo off
REM 开发模式启动脚本（Windows）

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo Starting Taskhub MCP Server in development mode...
python -m src.server --transport sse --host 0.0.0.0 --port 8000
pause