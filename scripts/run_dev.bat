@echo off
@chcp 65001 > nul
REM 开发模式启动脚本（Windows）

REM 创建必要的目录
if not exist "data" mkdir data
if not exist "logs" mkdir logs

echo Starting Taskhub MCP Server in development mode...
start "Taskhub Server" python "%~dp0launch.py" --transport sse --host 0.0.0.0 --port 8000 > server.log 2>&1

echo Waiting for server to start...
timeout /t 10 > nul

echo Checking server status at /api/v1/tasks...
curl http://localhost:8000/api/v1/tasks
