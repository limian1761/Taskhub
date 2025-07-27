import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.storage.json_store import JsonStore
from src.models.task import Task
from src.models.agent import Agent


class WebAdminServer:
    """Web管理界面服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.store = JsonStore()
        self.app = FastAPI(
            title="Taskhub Web Admin",
            description="Taskhub管理界面",
            version="2.0.0"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 设置模板目录
        template_dir = Path(__file__).parent / "templates"
        static_dir = Path(__file__).parent / "static"
        
        template_dir.mkdir(exist_ok=True)
        static_dir.mkdir(exist_ok=True)
        
        self.templates = Jinja2Templates(directory=str(template_dir))
        
        # 注册路由
        self._register_routes()
        
        # 如果静态文件目录存在，挂载静态文件
        if static_dir.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    def _register_routes(self):
        """注册路由"""
        
        @self.app.get("/")
        async def dashboard(request: Request):
            """管理面板首页"""
            return self.templates.TemplateResponse("dashboard.html", {"request": request})
        
        @self.app.get("/api/tasks")
        async def get_tasks():
            """获取所有任务"""
            try:
                tasks = self.store.list_tasks()
                return {
                    "success": True,
                    "data": [task.model_dump() for task in tasks]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/tasks/{task_id}")
        async def get_task(task_id: str):
            """获取单个任务详情"""
            task = self.store.get_task(task_id)
            if not task:
                raise HTTPException(status_code=404, detail="任务不存在")
            return {"success": True, "data": task.model_dump()}
        
        @self.app.post("/api/tasks")
        async def create_task(task_data: Dict[str, Any]):
            """创建新任务"""
            try:
                task = Task(**task_data)
                success = self.store.save_task(task)
                return {"success": success, "data": task.model_dump()}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.delete("/api/tasks/{task_id}")
        async def delete_task(task_id: str, force: bool = False):
            """删除任务"""
            try:
                task = self.store.get_task(task_id)
                if not task:
                    raise HTTPException(status_code=404, detail="任务不存在")
                
                # 检查依赖关系
                if not force:
                    all_tasks = self.store.list_tasks()
                    dependent_tasks = []
                    
                    for t in all_tasks:
                        if task_id in t.depends_on:
                            dependent_tasks.append(t.id)
                    
                    if dependent_tasks:
                        return {
                            "success": False,
                            "error": f"任务被其他任务依赖: {dependent_tasks}",
                            "dependent_tasks": dependent_tasks
                        }
                
                # 清理代理关联
                if task.assignee and task.status == "claimed":
                    agent = self.store.get_agent(task.assignee)
                    if agent and task_id in agent.current_tasks:
                        agent.current_tasks.remove(task_id)
                        self.store.update_agent(task.assignee, current_tasks=agent.current_tasks)
                
                success = self.store.delete_task(task_id)
                return {"success": success, "message": "任务已删除"}
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/agents")
        async def get_agents():
            """获取所有代理"""
            try:
                agents = self.store.list_agents()
                return {
                    "success": True,
                    "data": [agent.model_dump() for agent in agents]
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/agents/{agent_id}")
        async def get_agent(agent_id: str):
            """获取单个代理详情"""
            agent = self.store.get_agent(agent_id)
            if not agent:
                raise HTTPException(status_code=404, detail="代理不存在")
            return {"success": True, "data": agent.model_dump()}
        
        @self.app.post("/api/agents")
        async def create_agent(agent_data: Dict[str, Any]):
            """创建新代理"""
            try:
                agent = Agent(**agent_data)
                success = self.store.save_agent(agent)
                return {"success": success, "data": agent.model_dump()}
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        @self.app.get("/api/stats")
        async def get_stats():
            """获取系统统计信息"""
            try:
                tasks = self.store.list_tasks()
                agents = self.store.list_agents()
                
                task_stats = {
                    "total": len(tasks),
                    "pending": len([t for t in tasks if t.status == "pending"]),
                    "claimed": len([t for t in tasks if t.status == "claimed"]),
                    "completed": len([t for t in tasks if t.status == "completed"]),
                    "failed": len([t for t in tasks if t.status == "failed"])
                }
                
                agent_stats = {
                    "total": len(agents),
                    "active": len([a for a in agents if a.status == "active"]),
                    "busy": len([a for a in agents if a.current_tasks])
                }
                
                return {
                    "success": True,
                    "data": {
                        "tasks": task_stats,
                        "agents": agent_stats,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    def run(self):
        """启动Web服务器"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )


if __name__ == "__main__":
    server = WebAdminServer()
    server.run()