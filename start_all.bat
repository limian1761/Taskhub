@echo off
chcp 65001 > nul
setlocal

:: This script starts all Taskhub services.
:: It launches separate processes for the API service and the MCP service.

:: Suppress websockets deprecation warnings globally
set PYTHONWARNINGS=ignore::DeprecationWarning

set PYTHONPATH=%~dp0src;%PYTHONPATH%
title Taskhub Services

:: Start API service
start "Taskhub API" python -m taskhub api --host localhost --port 8001

:: Start MCP service
start "Taskhub MCP" python -m taskhub mcp --host localhost --port 8000

echo.
echo Taskhub services have been started in separate windows.
echo API service: http://localhost:8001
echo MCP service: http://localhost:8000
endlocal
