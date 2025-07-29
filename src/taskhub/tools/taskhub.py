import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from ..models.task import Task
from ..models.agent import Agent
from ..models.report import ReportSubmitParams, Report, ReportListParams
from ..storage.sqlite_store import SQLiteStore
from ..utils.id_generator import IDGenerator

# 全局存储实例
store = SQLiteStore()

class TaskListParams(BaseModel):
    """task_list工具参数"""
    status: Optional[str] = Field(None, description="任务状态过滤")
    capability: Optional[str] = Field(None, description="能力要求过滤")


class TaskClaimParams(BaseModel):
    """task_claim工具参数"""
    task_id: str = Field(..., description="任务ID")
    agent_id: str = Field(..., description="代理ID")
    lease_duration_minutes: int = Field(default=30, description="租约持续时间（分钟）")


class ReportSubmitParams(BaseModel):
    """report_submit工具参数"""
    task_id: str = Field(..., description="任务ID")
    agent_id: str = Field(..., description="代理ID")
    status: str = Field(..., description="任务状态")
    details: Optional[str] = Field(None, description="报告详情")
    result: Optional[str] = Field(None, description="执行结果")


class TaskPublishParams(BaseModel):
    """task_publish工具参数"""
    name: str = Field(..., description="任务名称")
    details: str = Field(..., description="任务详情")
    capability: str = Field(..., description="所需能力")
    depends_on: List[str] = Field(default_factory=list, description="依赖任务ID列表")
    parent_task_id: Optional[str] = Field(None, description="父任务ID")
    created_by: str = Field(..., description="任务创建者ID")
    candidates: List[str] = Field(default_factory=list, description="候选代理ID列表")


class TaskDeleteParams(BaseModel):
    """task_delete工具参数"""
    task_id: str = Field(..., description="任务ID")
    force: bool = Field(default=False, description="是否强制删除")


class ReportEvaluateParams(BaseModel):
    """report_evaluate工具参数"""
    report_id: str = Field(..., description="报告ID")
    score: int = Field(..., description="评价分数 0-100", ge=0, le=100)
    reputation_change: int = Field(..., description="声望值变化")
    feedback: str = Field(..., description="评价反馈")
    capability_updates: Dict[str, int] = Field(default_factory=dict, description="能力等级更新")


class TaskArchiveParams(BaseModel):
    """task_archive工具参数"""
    task_id: str = Field(..., description="任务ID")


class TaskSuggestParams(BaseModel):
    """task_suggest_agents工具参数"""
    agent_id: str = Field(..., description="代理ID")
    limit: int = Field(default=5, description="返回任务数量限制")


class AgentRegisterParams(BaseModel):
    """agent_register工具参数"""
    capabilities: List[str] = Field(..., description="代理能力列表")
    capability_levels: Dict[str, int] = Field(default_factory=dict, description="能力等级映射")


class TaskhubAPI:
    def __init__(self):
        pass

    async def task_list(self, params: TaskListParams) -> List[Dict[str, Any]]:
        return await task_list(params)

    async def task_claim(self, params: TaskClaimParams) -> Dict[str, Any]:
        return await task_claim(params)

    async def report_submit(self, params: ReportSubmitParams) -> Dict[str, Any]:
        return await report_submit(params)

    async def task_publish(self, params: TaskPublishParams) -> Dict[str, Any]:
        return await task_publish(params)

    async def task_delete(self, params: TaskDeleteParams) -> Dict[str, Any]:
        return await task_delete(params)

    async def report_evaluate(self, params: ReportEvaluateParams) -> Dict[str, Any]:
        return await report_evaluate(params)

    async def task_archive(self, params: TaskArchiveParams) -> Dict[str, Any]:
        return await task_archive(params)

    async def task_suggest_agents(self, params: TaskSuggestParams) -> List[Dict[str, Any]]:
        return await task_suggest_agents(params)

    async def agent_register(self, params: AgentRegisterParams) -> Dict[str, Any]:
        return await agent_register(params)


# --- 工具函数实现 ---

async def task_list(params: TaskListParams) -> List[Dict[str, Any]]:
    """
    列出所有任务
    
    Args:
        params: 任务过滤参数
        
    Returns:
        任务列表
    """
    tasks = store.list_tasks(
        status=params.status,
        capability=params.capability
    )
    return [task.model_dump() for task in tasks]


async def task_publish(params: TaskPublishParams) -> Dict[str, Any]:
    """
    发布任务
    
    Args:
        params: 任务参数
        
    Returns:
        发布结果
    """
    # 验证参数
    if not params.name or not params.details:
        return {"success": False, "error": "任务名称和详情不能为空"}
    
    # 创建任务
    task_id = IDGenerator.generate_task_id()
    now = datetime.utcnow()
    task = Task(
        id=task_id,
        name=params.name,
        details=params.details,
        capability=params.capability,
        depends_on=params.depends_on,
        parent_task_id=params.parent_task_id,
        created_by=params.created_by,
        created_at=now,
        updated_at=now
    )
    
    # 保存任务
    success = store.save_task(task)
    if not success:
        return {"success": False, "error": "任务保存失败"}
    
    return {"success": True, "task_id": task_id}


async def task_claim(params: TaskClaimParams) -> Dict[str, Any]:
    """
    认领任务
    
    Args:
        params: 包含task_id、agent_id和租约持续时间
        
    Returns:
        认领结果，包含成功状态和任务信息
    """
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    agent = store.get_agent(params.agent_id)
    if not agent:
        return {"success": False, "error": "代理不存在"}
    
    # 检查任务状态
    if task.status != "pending":
        return {"success": False, "error": f"任务状态为{task.status}，无法认领"}
    
    # 检查租约是否已过期
    now = datetime.utcnow()
    if task.lease_expires_at and task.lease_expires_at > now:
        return {"success": False, "error": "任务已被其他代理认领"}
    
    # 检查依赖任务是否已完成
    if task.depends_on:
        for dep_id in task.depends_on:
            dep_task = store.get_task(dep_id)
            if not dep_task or dep_task.status != "completed":
                return {"success": False, "error": f"依赖任务未完成: {dep_id}"}
    
    # 生成租约
    lease_id = IDGenerator.generate_lease_id()
    lease_expires_at = now + timedelta(minutes=params.lease_duration_minutes)
    
    # 更新任务
    success = store.update_task(
        params.task_id,
        status="claimed",
        assignee=params.agent_id,
        lease_id=lease_id,
        lease_expires_at=lease_expires_at.isoformat()
    )
    
    if success:
        # 更新代理当前任务列表
        agent.current_tasks.append(params.task_id)
        store.update_agent(params.agent_id, current_tasks=agent.current_tasks)
        
        return {"success": True, "task": task.model_dump()}
    else:
        return {"success": False, "error": "任务认领失败"}


async def report_submit(params: ReportSubmitParams) -> Dict[str, Any]:
    """
    提交任务报告
    
    Args:
        params: 报告参数
        
    Returns:
        提交结果
    """
    # 验证任务存在且已被认领
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    if task.status != "claimed":
        return {"success": False, "error": "任务未被认领"}
    
    if task.assignee != params.agent_id:
        return {"success": False, "error": "任务不属于该代理"}
    
    # 创建报告
    report_id = IDGenerator.generate_report_id()
    now = datetime.utcnow()
    report = Report(
        id=report_id,
        task_id=params.task_id,
        agent_id=params.agent_id,
        status="submitted",
        details=params.details,
        result=params.result,
        created_at=now.isoformat(),
        updated_at=now.isoformat()
    )
    
    # 保存报告
    success = store.save_report(report)
    if not success:
        return {"success": False, "error": "报告保存失败"}
    
    # 更新任务状态
    task_status = "completed" if params.status == "completed" else "failed"
    store.update_task(params.task_id, status=task_status)
    
    # 更新代理信息
    agent = store.get_agent(params.agent_id)
    if agent:
        if params.task_id in agent.current_tasks:
            agent.current_tasks.remove(params.task_id)
            
        if params.status == "completed":
            agent.completed_tasks += 1
        else:
            agent.failed_tasks += 1
            
        store.update_agent(params.agent_id, 
                          current_tasks=agent.current_tasks,
                          completed_tasks=agent.completed_tasks,
                          failed_tasks=agent.failed_tasks)
    
    return {"success": True, "report_id": report_id}


async def report_list(params: ReportListParams) -> List[Dict[str, Any]]:
    """
    获取报告列表
    
    Args:
        params: 筛选参数
        
    Returns:
        报告列表
    """
    reports = store.list_reports(
        task_id=params.task_id,
        agent_id=params.agent_id,
        status=params.status,
        limit=params.limit
    )
    return [report.model_dump() for report in reports]


async def task_delete(params: TaskDeleteParams) -> Dict[str, Any]:
    """
    删除任务
    
    Args:
        params: 任务ID和是否强制删除
        
    Returns:
        删除结果
    """
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    # 检查是否有其他任务依赖此任务
    if not params.force:
        all_tasks = store.list_tasks()
        for t in all_tasks:
            if params.task_id in t.depends_on:
                return {"success": False, "error": f"任务被其他任务 {t.id} 依赖，无法删除"}
    
    # 如果任务已被认领，从代理中移除
    if task.assignee and task.status == "claimed":
        agent = store.get_agent(task.assignee)
        if agent and params.task_id in agent.current_tasks:
            agent.current_tasks.remove(params.task_id)
            store.update_agent(task.assignee, current_tasks=agent.current_tasks)
    
    # 删除任务
    success = store.delete_task(params.task_id)
    if success:
        return {"success": True, "message": "任务删除成功"}
    else:
        return {"success": False, "error": "任务删除失败"}


async def report_evaluate(params: ReportEvaluateParams) -> Dict[str, Any]:
    """
    评价报告
    
    Args:
        params: 评价参数
        
    Returns:
        评价结果
    """
    # 获取报告
    report = store.get_report(params.report_id)
    if not report:
        return {"success": False, "error": "报告不存在"}
    
    # 更新报告状态
    now = datetime.utcnow()
    evaluation = ReportEvaluation(
        score=params.score,
        reputation_change=params.reputation_change,
        feedback=params.feedback,
        evaluator_id=os.environ.get("AGENT_ID", "system"),
        capability_updates=params.capability_updates,
        evaluated_at=now.isoformat()
    )
    
    success = store.update_report(
        params.report_id,
        status="reviewed",
        evaluation=evaluation.model_dump()
    )
    
    if not success:
        return {"success": False, "error": "报告评价失败"}
    
    # 更新代理声望和能力等级
    agent = store.get_agent(report.agent_id)
    if agent:
        agent.reputation += params.reputation_change
        
        # 更新能力等级
        for capability, level in params.capability_updates.items():
            agent.capability_levels[capability] = level
            
        store.update_agent(
            report.agent_id,
            reputation=agent.reputation,
            capability_levels=agent.capability_levels
        )
    
    return {"success": True, "report": report.model_dump()}


async def task_archive(params: TaskArchiveParams) -> Dict[str, Any]:
    """
    归档任务
    
    Args:
        params: 任务ID
        
    Returns:
        归档结果
    """
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    # 检查任务状态
    if task.status not in ["completed", "failed"]:
        return {"success": False, "error": "只有已完成或失败的任务才能归档"}
    
    # 更新任务状态
    success = store.update_task(params.task_id, is_archived=True, status="archived")
    if success:
        return {"success": True, "message": "任务归档成功"}
    else:
        return {"success": False, "error": "任务归档失败"}


async def task_suggest_agents(params: TaskSuggestParams) -> List[Dict[str, Any]]:
    """
    为代理推荐任务
    
    Args:
        params: 代理ID和限制数量
        
    Returns:
        推荐任务列表
    """
    # 获取代理
    agent = store.get_agent(params.agent_id)
    if not agent:
        return []
    
    # 获取所有待处理任务
    pending_tasks = store.list_tasks(status="pending")
    
    # 筛选可用任务（依赖已完成的任务）
    available_tasks = []
    for task in pending_tasks:
        # 检查依赖任务是否已完成
        deps_satisfied = True
        for dep_id in task.depends_on:
            dep_task = store.get_task(dep_id)
            if not dep_task or dep_task.status != "completed":
                deps_satisfied = False
                break
        
        if deps_satisfied:
            available_tasks.append(task)
    
    # 根据代理能力和声望排序
    available_tasks.sort(key=lambda t: (
        # 优先匹配代理具备的能力
        t.capability in agent.capabilities,
        # 如果能力匹配，优先匹配代理能力等级高的任务
        agent.capability_levels.get(t.capability, 0) if t.capability in agent.capabilities else 0,
        # 代理声望越高，优先级越高
        agent.reputation,
        # 任务创建时间越早，优先级越高
        t.created_at
    ), reverse=True)
    
    # 返回前limit个任务
    return [task.model_dump() for task in available_tasks[:params.limit]]


async def agent_register(params: AgentRegisterParams) -> Dict[str, Any]:
    """
    代理注册
    
    Args:
        params: 包含capabilities和capability_levels
        
    Returns:
        注册结果
    """
    # 从环境变量获取代理ID和名称
    agent_id = os.environ.get("AGENT_ID")
    agent_name = os.environ.get("AGENT_NAME", f"Agent-{IDGenerator._generate_random_string(8)}")
    
    if not agent_id:
        return {"success": False, "error": "AGENT_ID环境变量未设置"}
    
    # 检查代理是否已存在
    existing_agent = store.get_agent(agent_id)
    
    # 创建或更新代理
    now = datetime.utcnow()
    
    if existing_agent:
        # 更新现有代理
        agent = existing_agent
        agent.capabilities = params.capabilities
        agent.capability_levels = params.capability_levels
        agent.updated_at = now
        is_new = False
    else:
        # 创建新代理
        agent = Agent(
            id=agent_id,
            name=agent_name,
            capabilities=params.capabilities,
            capability_levels=params.capability_levels,
            reputation=100,  # 初始声望值
            current_tasks=[],
            completed_tasks=0,
            failed_tasks=0,
            created_at=now,
            updated_at=now
        )
        is_new = True
    
    # 保存代理
    success = store.save_agent(agent)
    if not success:
        return {"success": False, "error": "代理保存失败"}
    
    return {
        "success": True, 
        "agent_id": agent_id, 
        "message": "代理注册成功" if is_new else "代理信息更新成功",
        "agent": agent.model_dump(),
        "is_new": is_new
    }