import json
import logging
import logging.config
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.tools.taskhub import (
    hunter_list,
    hunter_register,
    hunter_study,
    knowledge_add,
    knowledge_list,
    report_evaluate,
    report_list,
    task_archive,
    task_claim,
    task_delete,
    task_list,
)

# ... (logging setup remains the same)

app = FastAPI(title="Taskhub API Server", description="API and Web server for Taskhub.")
# ... (middleware and static files remain the same)

async def get_db(namespace: str = Query("default", description="The namespace to operate on.")):
    # ... (get_db remains the same)

# ... (log_request_headers remains the same)

@app.get("/", response_class=HTMLResponse)
async def root():
    # ... (root remains the same)

@app.get("/api/tasks")
async def get_tasks(
    status: str | None = None,
    required_skill: str | None = None,
    hunter_id: str | None = None,
    db: SQLiteStore = Depends(get_db),
):
    try:
        tasks = await task_list(db, status, required_skill, hunter_id)
        return {"tasks": [task.dict() for task in tasks]}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/hunters")
async def get_hunters(db: SQLiteStore = Depends(get_db)):
    try:
        hunters = await hunter_list(db)
        return {"hunters": [hunter.dict() for hunter in hunters]}
    except Exception as e:
        logger.error(f"Error listing hunters: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... (get_reports, get_knowledge remain the same)

@app.post("/api/tasks/{task_id}/claim")
async def claim_task(task_id: str, hunter_id: str, db: SQLiteStore = Depends(get_db)):
    try:
        task = await task_claim(db, task_id, hunter_id)
        return {"task": task.dict()}
    except Exception as e:
        logger.error(f"Error claiming task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... (archive_task, delete_task remain the same)

@app.post("/api/hunters/register")
async def register_hunter(hunter_data: dict[str, Any], db: SQLiteStore = Depends(get_db)):
    try:
        hunter = await hunter_register(db, hunter_data["hunter_id"], hunter_data.get("skills"))
        return {"hunter": hunter.dict()}
    except Exception as e:
        logger.error(f"Error registering hunter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/{report_id}/evaluate")
async def evaluate_report(report_id: str, evaluation: dict[str, Any], db: SQLiteStore = Depends(get_db)):
    try:
        report = await report_evaluate(
            db,
            report_id,
            evaluation["score"],
            evaluation["feedback"],
            evaluation.get("skill_updates"),
        )
        return {"report": report.dict()}
    except Exception as e:
        logger.error(f"Error evaluating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/hunters/{hunter_id}/study/{knowledge_id}")
async def study_knowledge(hunter_id: str, knowledge_id: str, db: SQLiteStore = Depends(get_db)):
    try:
        hunter = await hunter_study(db, hunter_id, knowledge_id)
        return {"hunter": hunter.dict()}
    except Exception as e:
        logger.error(f"Error studying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ... (add_knowledge remains the same)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)