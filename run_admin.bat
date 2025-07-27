
@echo off
echo Starting Taskhub Admin Panel...
call .\.venv\Scripts\activate.bat
uvicorn src.admin_server:app --host 127.0.0.1 --port 8001
deactivate
