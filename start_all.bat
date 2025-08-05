@echo off
chcp 65001 > nul
setlocal

:: Add project root directory to Python path for proper module resolution
set PYTHONPATH=%~dp0;%PYTHONPATH%

echo Starting Taskhub services with specified ports...
echo.

REM Set title for this launcher window
title Taskhub Service Launcher

REM Start main Taskhub MCP service
echo Starting Main Taskhub Server on port 3000...
start "Taskhub Main Server" cmd /c "cd /d %~dp0 && python -m taskhub --transport sse --host 0.0.0.0 --port 3000"

REM Start Admin service
echo Starting API Server on port 8000...
start "Taskhub API Server" cmd /c "uvicorn src.taskhub.api:app --host 0.0.0.0 --port 8000 --reload --reload-dir src"

echo.
echo All services have been launched in separate windows.
echo You can close this window.

endlocal