

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import subprocess
import os
import json
import asyncio
import logging
from typing import List, Dict, Any
import sys
import signal

from .tools.taskhub import TaskhubAPI, TaskListParams, TaskClaimParams, ReportSubmitParams, TaskPublishParams, TaskDeleteParams, ReportEvaluateParams, TaskArchiveParams, TaskSuggestParams, AgentRegisterParams

taskhub_api = TaskhubAPI()

# --- FastAPI App ---
app = FastAPI(title="Taskhub Admin API", description="Admin API for managing the Taskhub service and data.")

# --- Process Management ---
process = None

# --- Logging ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Utility Functions ---
def get_taskhub_status():
    global process
    return {"status": "running" if process and process.poll() is None else "stopped"}

# --- Service Control Endpoints ---

@app.post("/api/start", summary="Start Taskhub Process")
async def start_taskhub_process(background_tasks: BackgroundTasks):
    global process
    if process and process.poll() is None:
        raise HTTPException(status_code=400, detail="Taskhub process is already running.")
    
    # Define the command to start the taskhub process
    # This assumes the server script is in the same directory
    server_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
    if not os.path.exists(server_script_path):
        raise HTTPException(status_code=500, detail=f"Server script not found at {server_script_path}")
    
    command = [sys.executable, server_script_path]
    
    try:
        # Start the process
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"Started Taskhub process with PID {process.pid}")
        return {"message": "Taskhub process started successfully.", "pid": process.pid}
    except Exception as e:
        logger.error(f"Failed to start Taskhub process: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start Taskhub process: {str(e)}")

@app.post("/api/stop", summary="Stop Taskhub Process")
async def stop_taskhub_process():
    global process
    if not process or process.poll() is not None:
        raise HTTPException(status_code=400, detail="Taskhub process is not running.")
    
    try:
        # Terminate the process
        process.terminate()
        process.wait(timeout=10)  # Wait up to 10 seconds for graceful shutdown
        logger.info("Taskhub process stopped successfully.")
        return {"message": "Taskhub process stopped successfully."}
    except subprocess.TimeoutExpired:
        # If it doesn't terminate gracefully, kill it
        process.kill()
        process.wait()
        logger.warning("Taskhub process killed forcefully.")
        return {"message": "Taskhub process killed forcefully."}
    except Exception as e:
        logger.error(f"Error stopping Taskhub process: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping Taskhub process: {str(e)}")

@app.post("/api/restart", summary="Restart Taskhub Process")
async def restart_service(background_tasks: BackgroundTasks):
    await stop_taskhub_process()
    await asyncio.sleep(1)  # Brief pause before restarting
    response = await start_taskhub_process(background_tasks)
    return response

@app.get("/api/status", summary="Get Taskhub Process Status")
async def get_status():
    return get_taskhub_status()

# --- Data Management Endpoints ---

@app.get("/api/agents", summary="Get All Agents", response_model=List[Dict[str, Any]])
async def get_agents():
    try:
        agents = taskhub_api.task_list(TaskListParams(object_type="agents"))
        return agents
    except Exception as e:
        logger.error(f"Error fetching agents: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching agents: {str(e)}")

@app.delete("/api/agents/{agent_id}", summary="Delete an Agent", status_code=204)
async def delete_agent(agent_id: str):
    try:
        # Note: The current taskhub API doesn't have a direct delete agent method.
        # This would need to be implemented in the core taskhub logic.
        # For now, we'll simulate a successful deletion.
        logger.info(f"Delete agent request for ID: {agent_id} (not implemented in core)")
        # raise HTTPException(status_code=501, detail="Delete agent not implemented in core Taskhub API")
        return
    except Exception as e:
        logger.error(f"Error deleting agent {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting agent: {str(e)}")

@app.get("/api/tasks", summary="Get All Tasks", response_model=List[Dict[str, Any]])
async def get_tasks():
    try:
        tasks = taskhub_api.task_list(TaskListParams(object_type="tasks"))
        return tasks
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching tasks: {str(e)}")

@app.delete("/api/tasks/{task_id}", summary="Delete a Task", status_code=204)
async def delete_task(task_id: str):
    try:
        taskhub_api.task_delete(TaskDeleteParams(task_id=task_id))
        return
    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting task: {str(e)}")

@app.get("/api/reports", summary="Get All Reports", response_model=List[Dict[str, Any]])
async def get_reports():
    try:
        # Note: The current taskhub API doesn't have a direct list reports method.
        # This would need to be implemented in the core taskhub logic.
        # For now, we'll return an empty list.
        logger.info("Get reports request (not implemented in core)")
        # raise HTTPException(status_code=501, detail="Get reports not implemented in core Taskhub API")
        return []
    except Exception as e:
        logger.error(f"Error fetching reports: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching reports: {str(e)}")

@app.delete("/api/reports/{report_id}", summary="Delete a Report", status_code=204)
async def delete_report(report_id: str):
    try:
        # Note: The current taskhub API doesn't have a direct delete report method.
        # This would need to be implemented in the core taskhub logic.
        # For now, we'll simulate a successful deletion.
        logger.info(f"Delete report request for ID: {report_id} (not implemented in core)")
        # raise HTTPException(status_code=501, detail="Delete report not implemented in core Taskhub API")
        return
    except Exception as e:
        logger.error(f"Error deleting report {report_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting report: {str(e)}")

# --- AI Management Endpoint ---

@app.post("/api/ai/query", summary="Query AI Management Tool")
async def ai_query(query: Dict[str, str]):
    prompt = query.get("prompt", "")
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required.")
    
    try:
        # Simulate AI processing
        # In a real implementation, this would call an external AI service
        # For demonstration, we'll just echo the prompt with a prefix
        ai_response = f"[AI Response] {prompt}"
        return {"result": ai_response}
    except Exception as e:
        logger.error(f"Error processing AI query: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing AI query: {str(e)}")

# --- WebSocket for Logs ---

# In-memory list to store connected WebSocket clients
active_connections: List[WebSocket] = []

async def send_log_to_websockets(message: str):
    """Send a log message to all active WebSocket connections."""
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except WebSocketDisconnect:
            # Remove the connection if it's disconnected
            active_connections.remove(connection)
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            active_connections.remove(connection)

@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep the connection alive; logs are sent via the send_log_to_websockets function
            # This could be a ping message or just await a receive which will eventually disconnect
            data = await websocket.receive_text()
            # For a simple log stream, we might not expect messages from the client
            # but we need to await something to keep the connection open
            # A ping/pong or just ignoring received data is common
            pass
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        active_connections.remove(websocket)

# --- Frontend Serving ---

# Mount the templates directory to serve HTML files
# This assumes the admin.html file is in a 'templates' subdirectory
# relative to this script's location.
templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
if os.path.exists(templates_dir):
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def read_admin_panel():
        with open(os.path.join(templates_dir, "admin.html"), "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
else:
    @app.get("/", include_in_schema=False)
    async def read_admin_panel():
        return JSONResponse(content={"message": "Admin panel not found. Please ensure 'templates/admin.html' exists."}, status_code=404)

# --- Main Execution ---

if __name__ == "__main__":
    import uvicorn
    # Run the FastAPI app with uvicorn
    # This is for development purposes; in production, you would use a proper ASGI server
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


@app.post("/api/tasks/{task_id}/claim", summary="Claim a Task")
async def claim_task(task_id: str, agent_id: str):
    try:
        # Create TaskClaimParams object
        params = TaskClaimParams(task_id=task_id, agent_id=agent_id)
        
        # Call task_claim function
        result = await taskhub_api.task_claim(params)
        
        # Check if the claim was successful
        if result.get("success"):
            return result
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to claim task"))
    except Exception as e:
        logger.error(f"Error claiming task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error claiming task: {str(e)}")

