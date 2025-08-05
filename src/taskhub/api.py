import json
import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent))

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

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": "%(levelprefix)s %(asctime)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "taskhub": {"handlers": ["default"], "level": "INFO"},
        },
    }
)

logger = logging.getLogger("taskhub")

app = FastAPI(title="Taskhub API Server", description="API and Web server for Taskhub.")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")


async def get_db(namespace: str = Query("default", description="The namespace to operate on.")):
    return SQLiteStore(namespace)


@app.middleware("http")
async def log_request_headers(request: Request, call_next):
    logger.info(f"Request received: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response sent: {response.status_code}")
    return response


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Taskhub API Server</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Taskhub API Server</h1>
            <p>API is running successfully.</p>
            <p>Check out the <a href="/docs">API documentation</a></p>
        </body>
        </html>
        """
    )


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


@app.get("/api/reports")
async def get_reports(db: SQLiteStore = Depends(get_db)):
    try:
        reports = await report_list(db)
        return {"reports": [report.dict() for report in reports]}
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge")
async def get_knowledge(db: SQLiteStore = Depends(get_db)):
    try:
        knowledge = await knowledge_list(db)
        return {"knowledge": [knowledge_item.dict() for knowledge_item in knowledge]}
    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/claim")
async def claim_task(task_id: str, hunter_id: str, db: SQLiteStore = Depends(get_db)):
    try:
        task = await task_claim(db, task_id, hunter_id)
        return {"task": task.dict()}
    except Exception as e:
        logger.error(f"Error claiming task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/archive")
async def archive_task(task_id: str, db: SQLiteStore = Depends(get_db)):
    try:
        task = await task_archive(db, task_id)
        return {"task": task.dict()}
    except Exception as e:
        logger.error(f"Error archiving task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/delete")
async def delete_task(task_id: str, db: SQLiteStore = Depends(get_db)):
    try:
        await task_delete(db, task_id)
        return {"message": "Task deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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


@app.post("/api/knowledge/add")
async def add_knowledge(knowledge_data: dict[str, Any], db: SQLiteStore = Depends(get_db)):
    try:
        knowledge_item = await knowledge_add(db, knowledge_data["knowledge_id"], knowledge_data["content"])
        return {"knowledge": knowledge_item.dict()}
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
