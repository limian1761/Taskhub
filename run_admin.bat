
@echo off

echo Starting Taskhub Admin Panel...

REM Check if virtual environment exists
if not exist ".\.venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found. Please run 'uv sync' first.
    exit /b 1
)

call .\.venv\Scripts\activate.bat

uvicorn taskhub.admin_server:app --host 127.0.0.1 --port 8001

deactivate

echo Taskhub Admin Panel stopped.
