

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

# --- Configuration ---
# Get the root directory of the project
ROOT_DIRECTORY = Path(__file__).parent.parent
# Path to the main Taskhub server script
TASKHUB_SCRIPT_PATH = ROOT_DIRECTORY / "src" / "web_server.py"
# Path to the admin panel template
ADMIN_TEMPLATE_PATH = ROOT_DIRECTORY / "src" / "templates" / "admin.html"
# Host and port for the admin server
ADMIN_HOST = "127.0.0.1"
ADMIN_PORT = 8001

# --- State ---
# Global variable to hold the Taskhub process
taskhub_process: Optional[subprocess.Popen] = None
# Global variable to hold the log queue
log_queue: Optional[asyncio.Queue] = None

# --- FastAPI App ---
app = FastAPI()


# --- Process Management ---
async def read_stream(stream, queue):
    """Read lines from a stream and put them into a queue."""
    while True:
        line = await stream.readline()
        if line:
            await queue.put(line.decode("utf-8"))
        else:
            break


async def start_taskhub_process():
    """Starts the Taskhub server as a subprocess and monitors its output."""
    global taskhub_process, log_queue
    if taskhub_process and taskhub_process.poll() is None:
        return  # Process is already running

    log_queue = asyncio.Queue()
    command = [sys.executable, str(TASKHUB_SCRIPT_PATH)]

    # Create the subprocess
    taskhub_process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
    )

    # Create tasks to read stdout and stderr
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


# --- API Endpoints ---
@app.post("/api/start")
async def start_service():
    """Endpoint to start the Taskhub service."""
    if taskhub_process and taskhub_process.poll() is None:
        raise HTTPException(status_code=400, detail="Service is already running.")
    await start_taskhub_process()
    return {"status": "starting"}


@app.post("/api/stop")
async def stop_service():
    """Endpoint to stop the Taskhub service."""
    if not taskhub_process or taskhub_process.poll() is not None:
        raise HTTPException(status_code=400, detail="Service is not running.")
    return stop_taskhub_process()


@app.post("/api/restart")
async def restart_service():
    """Endpoint to restart the Taskhub service."""
    if taskhub_process and taskhub_process.poll() is None:
        stop_taskhub_process()
        await asyncio.sleep(1)  # Give it a moment to shut down
    await start_taskhub_process()
    return {"status": "restarting"}


@app.get("/api/status")
async def get_status():
    """Endpoint to get the current status of the Taskhub service."""
    if taskhub_process and taskhub_process.poll() is None:
        return {"status": "running"}
    return {"status": "stopped"}


@app.websocket("/ws/logs")
async def websocket_log_endpoint(websocket: WebSocket):
    """WebSocket endpoint to stream logs."""
    await websocket.accept()
    if not log_queue:
        await websocket.send_text("Log queue not available. Is the service running?\n")
        await websocket.close()
        return

    # Create a task to send queued logs
    async def send_logs():
        while True:
            try:
                log_entry = await asyncio.wait_for(log_queue.get(), timeout=1.0)
                await websocket.send_text(log_entry)
                log_queue.task_done()
            except asyncio.TimeoutError:
                # Check if the websocket is still alive
                try:
                    await websocket.send_text("") # Ping
                except WebSocketDisconnect:
                    break
            except WebSocketDisconnect:
                break

    send_task = asyncio.create_task(send_logs())
    try:
        # Keep the connection alive, waiting for the client to disconnect
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        send_task.cancel()
        print("Client disconnected from log stream.")


@app.get("/", response_class=HTMLResponse)
async def get_admin_panel():
    """Serves the admin panel HTML file."""
    if not ADMIN_TEMPLATE_PATH.exists():
        raise HTTPException(status_code=404, detail="Admin panel template not found.")
    return FileResponse(ADMIN_TEMPLATE_PATH)


# --- Main Execution ---
if __name__ == "__main__":
    # Stop the managed process when the admin server shuts down
    try:
        uvicorn.run(app, host=ADMIN_HOST, port=ADMIN_PORT)
    finally:
        if taskhub_process:
            stop_taskhub_process()

