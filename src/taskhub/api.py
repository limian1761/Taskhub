import json
import sys
from pathlib import Path
from typing import Any

# 将src目录添加到Python路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

# 标准库导入
import logging
import logging.config

# 第三方库导入
import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 本地模块导入
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.context import get_store
from taskhub.services import (
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
    task_publish,
    discussion_service,
    get_task,
)

# 导入服务模块
import taskhub.services.hunter_service as hunter_service
import taskhub.services.task_service as task_service
import taskhub.services.knowledge_service as knowledge_service
import taskhub.services.report_service as report_service

# 从system_service导入具体函数
from taskhub.services.system_service import (
    get_task_interaction_graph,
    get_system_stats,
    get_all_tasks,
)

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="templates")

app = FastAPI(title="Taskhub API", version="0.1.0")

async def get_store(namespace: str = Query("default", description="The namespace for the database.")):
    """
    Dependency function to get a database store for a given namespace.
    Creates a new store instance for each request and closes it afterward.
    """
    db_path = f"data/{namespace}.db"
    store = SQLiteStore(db_path)
    try:
        await store.connect()
        yield store
    finally:
        await store.close()

# Request models
class DiscussionPostRequest(BaseModel):
    hunter_id: str
    content: str


@app.middleware("http")
async def log_request_headers(request: Request, call_next):
    logger.info(f"Request received: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response sent: {response.status_code}")
    
    # 添加命名空间和管理URL信息到响应头
    namespace = request.query_params.get("namespace", "default")
    management_url = f"{request.url.scheme}://{request.url.netloc}/?namespace={namespace}"
    
    # 添加管理URL到响应头
    response.headers["X-Taskhub-Management-URL"] = management_url
    response.headers["X-Taskhub-Namespace"] = namespace
    
    return response


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serves the main admin web interface."""
    logger.info("Root endpoint accessed")
    try:
        return templates.TemplateResponse("admin.html", {"request": request})
    except Exception as e:
        logger.error(f"Error rendering template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/system/task-graph", tags=["System"])
async def get_task_graph_data(
    store: SQLiteStore = Depends(get_store),
):
    """获取任务网络图数据"""
    return await get_task_interaction_graph(store)


@app.get("/api/system/stats", tags=["System"])
async def get_system_stats_api(store: SQLiteStore = Depends(get_store)):
    """获取仪表盘的统计数据"""
    return await get_system_stats(store)


@app.get("/api/system/tasks", tags=["System"])
async def get_all_tasks_api(store: SQLiteStore = Depends(get_store)):
    """获取所有任务的列表"""
    return await get_all_tasks(store)


@app.get("/api/tasks")
async def get_tasks(
    status: str | None = None,
    required_skill: str | None = None,
    hunter_id: str | None = None,
    db: SQLiteStore = Depends(get_store),
):
    try:
        tasks = await task_list(db, status, required_skill, hunter_id)
        return {"tasks": [task.model_dump() for task in tasks]}
    except Exception as e:
        logger.error(f"Error listing tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/hunters")
async def get_hunters(db: SQLiteStore = Depends(get_store)):
    try:
        hunters = await hunter_list(db)
        return {"hunters": [hunter.model_dump() for hunter in hunters]}
    except Exception as e:
        logger.error(f"Error listing hunters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports")
async def get_reports(db: SQLiteStore = Depends(get_store)):
    try:
        reports = await report_list(db)
        return {"reports": [report.model_dump() for report in reports]}
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge")
async def get_knowledge(db: SQLiteStore = Depends(get_store)):
    try:
        knowledge = await knowledge_list(db)
        return {"knowledge": [knowledge_item.model_dump() for knowledge_item in knowledge]}
    except Exception as e:
        logger.error(f"Error listing knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/claim")
async def claim_task(task_id: str, hunter_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        task = await task_claim(db, task_id, hunter_id)
        return {"task": task.model_dump()}
    except Exception as e:
        logger.error(f"Error claiming task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/archive")
async def archive_task(task_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        task = await task_archive(db, task_id)
        return {"task": task.model_dump()}
    except Exception as e:
        logger.error(f"Error archiving task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/{task_id}/delete")
async def delete_task(task_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        await task_delete(db, task_id)
        return {"message": "Task deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hunters/{hunter_id}/delete")
async def delete_hunter_endpoint(hunter_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        await hunter_service.delete_hunter(db, hunter_id)
        return {"message": f"Hunter {hunter_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting hunter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/{knowledge_id}/delete")
async def delete_knowledge_endpoint(knowledge_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        await knowledge_service.delete_knowledge(db, knowledge_id)
        return {"message": f"Knowledge item {knowledge_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reports/{report_id}/delete")
async def delete_report_endpoint(report_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        await report_service.delete_report(db, report_id)
        return {"message": f"Report {report_id} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task_by_id(task_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        task = await get_task(db, task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")
        return {"task": task.model_dump()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hunters/register")
async def register_hunter(hunter_data: dict[str, Any], db: SQLiteStore = Depends(get_store)):
    try:
        hunter = await hunter_register(db, hunter_data["hunter_id"], hunter_data.get("skills"))
        return {"hunter": hunter.model_dump()}
    except Exception as e:
        logger.error(f"Error registering hunter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reports/{report_id}/evaluate")
async def evaluate_report(report_id: str, evaluation: dict[str, Any], db: SQLiteStore = Depends(get_store)):
    try:
        report = await report_evaluate(
            db,
            report_id,
            evaluation["evaluator_id"],
            evaluation["score"],
            evaluation["feedback"],
            evaluation.get("skill_updates"),
        )
        return {"report": report.model_dump()}
    except Exception as e:
        logger.error(f"Error evaluating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/hunters/{hunter_id}/study/{knowledge_id}")
async def study_knowledge(hunter_id: str, knowledge_id: str, db: SQLiteStore = Depends(get_store)):
    try:
        hunter = await hunter_study(db, hunter_id, knowledge_id)
        return {"hunter": hunter.model_dump()}
    except Exception as e:
        logger.error(f"Error studying knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/knowledge/add")
async def add_knowledge(knowledge_data: dict[str, Any], db: SQLiteStore = Depends(get_store)):
    try:
        knowledge_item = await knowledge_add(db, knowledge_data["knowledge_id"], knowledge_data["content"])
        return {"knowledge": knowledge_item.model_dump()}
    except Exception as e:
        logger.error(f"Error adding knowledge: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/publish")
async def publish_task(task_data: dict[str, Any], db: SQLiteStore = Depends(get_store)):
    try:
        task = await task_publish(
            db,
            task_data["name"],
            task_data["details"],
            task_data["required_skill"],
            task_data["publisher_id"],
            task_data.get("depends_on"),
        )
        return {"task": task.model_dump()}
    except Exception as e:
        logger.error(f"Error publishing task: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/namespaces", tags=["System"])
async def list_namespaces():
    """Lists all available namespaces by scanning the data directory."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    return [f.stem for f in data_dir.glob("*.db")]


@app.get("/api/discussion", tags=["Discussion"])
async def get_discussion_messages(db: SQLiteStore = Depends(get_store)):
    logger.info("Getting discussion messages")
    try:
        messages = await db.get_latest_messages()
        logger.info(f"Retrieved {len(messages)} messages")
        return {"messages": [msg.model_dump() for msg in messages]}
    except Exception as e:
        logger.error(f"Error getting discussion messages: {e}")
        raise


@app.post("/api/discussion", tags=["Discussion"])
async def post_discussion_message(request: DiscussionPostRequest, db: SQLiteStore = Depends(get_store)):
    logger.info(f"Posting discussion message from hunter {request.hunter_id}")
    try:
        message = await discussion_service.post_message(db, request.hunter_id, request.content)
        logger.info(f"Posted message with id: {message.id}")
        return {"message": message.model_dump()}
    except Exception as e:
        logger.error(f"Error posting discussion message: {e}")
        raise



if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
