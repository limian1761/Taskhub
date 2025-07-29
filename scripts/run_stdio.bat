@echo off
@chcp 65001 > nul
REM stdio模式启动脚本

REM 获取脚本所在目录
set SCRIPT_DIR=%~dp0

REM 创建必要的目录
if not exist "%SCRIPT_DIR%..\data" mkdir "%SCRIPT_DIR%..\data"

echo Starting Taskhub MCP Server with stdio transport...
python "%SCRIPT_DIR%launch.py" --transport stdio