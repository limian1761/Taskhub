

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional, List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

# --- Project Imports ---
# Add the project root to the Python path to allow for absolute imports
ROOT_DIRECTORY = Path(__file__).parent.parent
sys.path.append(str(ROOT_DIRECTORY))

from src.storage.sqlite_store import SQLiteStore
from src.models.agent import Agent
from src.models.task import Task
from src.models.report import Report

# --- Configuration ---
TASKHUB_SCRIPT_PATH = ROOT_DIRECTORY / "src" / "web_server.py"
ADMIN_TEMPLATE_PATH = ROOT_DIRECTORY / "src" / "templates" / "admin.html"
ADMIN_HOST = "127.0.0.1"
ADMIN_PORT = 8001
DATA_DIR = ROOT_DIRECTORY / "data"

# --- State ---
taskhub_process: Optional[subprocess.Popen] = None
log_queue: Optional[asyncio.Queue] = None

# --- FastAPI App & DB ---
app = FastAPI()
db_store = SQLiteStore(data_dir=str(DATA_DIR))


# --- Process Management ---
async def read_stream(stream, queue):
    """Read lines from a stream and put them into a queue."""
    while True:
        line = await stream.readline()
        if line:
            await queue.put(line.decode("utf-8", errors="ignore"))
        else:
            break


async def start_taskhub_process():
    """Starts the Taskhub server as a subprocess and monitors its output."""
    global taskhub_process, log_queue
    if taskhub_process and taskhub_process.poll() is None:
        return

    log_queue = asyncio.Queue()
    command = [sys.executable, str(TASKHUB_SCRIPT_PATH)]

    taskhub_process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    asyncio.create_task(read_stream(taskhub_process.stdout, log_queue))
    asyncio.create_task(read_stream(taskhub_process.stderr, log_queue))
    await log_queue.put("Taskhub process started.\n")


def stop_taskhub_process():
    """Stops the Taskhub server process."""
    global taskhub_process, log_queue
    if taskhub_process and taskhub_process.poll() is None:
        try:
            if sys.platform == "win32":
                taskhub_process.send_signal(subprocess.CTRL_BREAK_EVENT)
            taskhub_process.terminate()
            taskhub_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            taskhub_process.kill()
        taskhub_process = None
        if log_queue:
            log_queue.put_nowait("Taskhub process stopped.\n")
    return {"status": "stopped"}


# --- API Endpoints for Service Control ---
@app.post("/api/start")
async def start_service():
    if taskhub_process and taskhub_process.poll() is None:
        raise HTTPException(status_code=400, detail="Service is already running.")
    await start_taskhub_process()
    return {"status": "starting"}


@app.post("/api/stop")
async def stop_service():
    if not taskhub_process or taskhub_process.poll() is not None:
        raise HTTPException(status_code=400, detail="Service is not running.")
    return stop_taskhub_process()


@app.post("/api/restart")
async def restart_service():
    if taskhub_process and taskhub_process.poll() is None:
        stop_taskhub_process()
        await asyncio.sleep(1)
    await start_taskhub_process()
    return {"status": "restarting"}


@app.get("/api/status")
async def get_status():
    if taskhub_process and taskhub_process.poll() is None:
        return {"status": "running"}
    return {"status": "stopped"}


# --- API Endpoints for Data Management ---
@app.get("/api/agents", response_model=List[Agent])
async def get_agents():
    """Get all agents, sorted by reputation."""
    try:
        agents = db_store.list_agents()
        # Sort agents by reputation in descending order
        agents.sort(key=lambda x: x.reputation, reverse=True)
        return agents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve agents: {e}")

@app.delete("/api/agents/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    """Delete an agent by ID."""
    if not db_store.delete_agent(agent_id):
        raise HTTPException(status_code=404, detail="Agent not found or could not be deleted.")
    return None


@app.get("/api/tasks", response_model=List[Task])
async def get_tasks():
    """Get all tasks."""
    try:
        return db_store.list_tasks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve tasks: {e}")

@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: str):
    """Delete a task by ID."""
    if not db_store.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found or could not be deleted.")
    return None


@app.get("/api/reports", response_model=List[Report])
async def get_reports():
    """Get all reports."""
    try:
        return db_store.list_reports()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve reports: {e}")

@app.delete("/api/reports/{report_id}", status_code=204)
async def delete_report(report_id: str):
    """Delete a report by ID."""
    if not db_store.delete_report(report_id):
        raise HTTPException(status_code=404, detail="Report not found or could not be deleted.")
    return None


# --- WebSocket for Logs ---
@app.websocket("/ws/logs")
async def websocket_log_endpoint(websocket: WebSocket):
    await websocket.accept()
    if not log_queue:
        await websocket.send_text("Log queue not available. Is the service running?\n")
        await websocket.close()
        return

    async def send_logs():
        while True:
            try:
                log_entry = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                await websocket.send_text(log_entry)
                log_queue.task_done()
            except asyncio.TimeoutError:
                try:
                    await websocket.send_text("")  # Ping
                except WebSocketDisconnect:
                    break
            except WebSocketDisconnect:
                break

    send_task = asyncio.create_task(send_logs())
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        send_task.cancel()
        print("Client disconnected from log stream.")


# --- Frontend Serving ---
@app.get("/", response_class=HTMLResponse)
async def get_admin_panel():
    if not ADMIN_TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Admin panel template not found.")
    return FileResponse(ADMIN_TEMPLATE_PATH)


# --- Main Execution ---
if __name__ == "__main__":
    try:
        uvicorn.run(app, host=ADMIN_HOST, port=ADMIN_PORT)
    finally:
        if taskhub_process:
            stop_taskhub_process()

