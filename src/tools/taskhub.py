import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from src.models.task import Task
from src.models.agent import Agent
from src.models.report import ReportSubmitParams, Report, ReportListParams
from src.storage.sqlite_store import SQLiteStore
from src.utils.id_generator import IDGenerator


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
    task_id: str = Field(..., description="要删除的任务ID")
    force: bool = Field(default=False, description="是否强制删除，即使有依赖关系")


class ReportEvaluateParams(BaseModel):
    """report_evaluate工具参数"""
    report_id: str = Field(..., description="报告ID")
    score: int = Field(..., ge=0, le=100, description="报告评分 0-100")
    reputation_change: int = Field(..., description="声望值变化")
    feedback: str = Field(..., description="评价反馈")
    capability_updates: Dict[str, int] = Field(default_factory=dict, description="能力等级更新")


class TaskArchiveParams(BaseModel):
    """task_archive工具参数"""
    task_id: str = Field(..., description="要归档的任务ID")


class TaskSuggestParams(BaseModel):
    """task_suggest_agents工具参数"""
    agent_id: str = Field(..., description="代理ID")
    limit: int = Field(default=5, description="返回任务数量限制")


class AgentRegisterParams(BaseModel):
    """agent_register工具参数"""
    capabilities: List[str] = Field(..., description="代理能力列表")
    capability_levels: Dict[str, int] = Field(default_factory=dict, description="能力等级映射")


async def task_list(params: TaskListParams) -> List[Dict[str, Any]]:
    """
    列出可用任务
    
    根据状态和能力要求过滤任务列表，返回符合要求的任务。
    
    Args:
        params: 包含status和capability过滤条件
        
    Returns:
        任务列表，每个任务包含完整信息
    """
    tasks = store.list_tasks(
        status=params.status,
        capability=params.capability
    )
    
    # 过滤掉已被认领且租约未过期的任务
    available_tasks = []
    now = datetime.utcnow()
    
    for task in tasks:
        if task.lease_expires_at and task.lease_expires_at > now:
            # 租约未过期，跳过
            continue
        
        # 检查依赖任务是否已完成
        if task.depends_on:
            all_deps_completed = True
            for dep_id in task.depends_on:
                dep_task = store.get_task(dep_id)
                if not dep_task or dep_task.status != "completed":
                    all_deps_completed = False
                    break
            
            if not all_deps_completed:
                continue
        
        available_tasks.append(task.model_dump())
    
    return available_tasks


async def task_claim(params: TaskClaimParams) -> Dict[str, Any]:
    """
    认领任务
    
    基于代理能力和声望的智能任务认领。当有候选者列表时，优先从候选者中选择最匹配的代理。
    
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
    
    # 检查代理能力
    if task.capability and task.capability not in agent.capabilities:
        return {"success": False, "error": f"代理不具备所需能力: {task.capability}"}
    
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
    
    # 智能匹配检查：如果任务有候选者列表，检查当前代理是否在列表中
    if task.candidates and params.agent_id not in task.candidates:
        return {"success": False, "error": "代理不在任务的候选者列表中"}
    
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
        
        return {
            "success": True,
            "task_id": params.task_id,
            "lease_id": lease_id,
            "expires_at": lease_expires_at.isoformat(),
            "matched_by": "candidates" if task.candidates else "open"
        }
    else:
        return {"success": False, "error": "更新任务失败"}


async def report_submit(params: ReportSubmitParams) -> Dict[str, Any]:
    """
    提交任务报告
    
    代理提交任务执行报告，包括状态、详细报告和附件。报告将存储在独立的SQLite数据库中。
    
    Args:
        params: 包含task_id、agent_id、status、report和attachments
        
    Returns:
        提交结果，包含成功状态、报告ID和任务信息
    """

    
    # 获取任务
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    if task.assignee != params.agent_id:
        return {"success": False, "error": "该任务不是由该代理认领"}
    
    if task.status != "claimed":
        return {"success": False, "error": "任务未被认领，无法提交报告"}
    
    # 检查租约是否过期
    now = datetime.utcnow()
    if task.lease_expires_at and task.lease_expires_at < now:
        return {"success": False, "error": "任务租约已过期"}
    
    # 创建报告
    report_id = IDGenerator.generate_report_id()
    report = Report(
        id=report_id,
        task_id=params.task_id,
        agent_id=params.agent_id,
        status=params.status,
        details=params.details,
        result=params.result or ""  # 可以扩展为更复杂的结果格式
    )
    
    # 保存报告
    report_saved = store.save_report(report)
    if not report_saved:
        return {"success": False, "error": "保存报告失败"}
    
    # 更新任务状态
    report_data = {
        "status": params.status,
        "updated_at": datetime.utcnow().isoformat()
    }
    
    task_updated = store.update_task(params.task_id, **report_data)
    if not task_updated:
        return {"success": False, "error": "更新任务状态失败"}
    
    # 如果任务完成或失败，更新代理统计
    if params.status in ["completed", "failed"]:
        agent = store.get_agent(params.agent_id)
        if agent:
            # 从当前任务中移除
            if params.task_id in agent.current_tasks:
                agent.current_tasks.remove(params.task_id)
            
            # 更新统计
            if params.status == "completed":
                completed_tasks = agent.completed_tasks + 1
                store.update_agent(
                    params.agent_id,
                    current_tasks=agent.current_tasks,
                    completed_tasks=completed_tasks
                )
            elif params.status == "failed":
                failed_tasks = agent.failed_tasks + 1
                store.update_agent(
                    params.agent_id,
                    current_tasks=agent.current_tasks,
                    failed_tasks=failed_tasks
                )
    
    return {
        "success": True,
        "report_id": report_id,
        "task_id": params.task_id,
        "status": params.status
    }


async def report_evaluate(params: ReportEvaluateParams) -> Dict[str, Any]:
    """
    报告评价
    
    对代理提交的报告进行评价，包括评分、声望值调整和代理能力更新。
    基于报告质量对代理进行奖惩。
    
    Args:
        params: 包含报告ID、评分、声望变化、反馈和能力更新
        
    Returns:
        评价结果，包含成功状态和更新后的信息
    """
    # 获取报告
    report = store.get_report(params.report_id)
    if not report:
        return {"success": False, "error": "报告不存在"}
    
    # 获取关联的任务
    task = store.get_task(report.task_id)
    if not task:
        return {"success": False, "error": "关联任务不存在"}
    
    if report.evaluation:
        return {"success": False, "error": "报告已评价过"}
    
    # 验证评价者身份（应该是任务创建者）
    if not task.created_by:
        return {"success": False, "error": "无法确定任务创建者"}
    
    # 获取提交报告的代理
    agent = store.get_agent(report.agent_id)
    if not agent:
        return {"success": False, "error": "提交代理不存在"}
    
    # 创建评价信息
    from src.models.report import ReportEvaluation
    evaluation = ReportEvaluation(
        score=params.score,
        reputation_change=params.reputation_change,
        feedback=params.feedback,
        evaluator_id=task.created_by,
        capability_updates=params.capability_updates
    )
    
    # 更新报告评价
    success = store.update_report(
        params.report_id,
        evaluation=evaluation.model_dump(),
        status="reviewed",
        updated_at=datetime.utcnow().isoformat()
    )
    
    if success:
        # 更新代理声望
        new_reputation = agent.reputation + params.reputation_change
        new_reputation = max(0, new_reputation)  # 声望值不能为负
        
        # 更新代理能力等级
        new_capability_levels = agent.capability_levels.copy()
        for capability, level_change in params.capability_updates.items():
            current_level = new_capability_levels.get(capability, 1)
            new_level = max(1, current_level + level_change)  # 能力等级至少为1
            new_capability_levels[capability] = new_level
        
        # 根据报告质量更新代理统计
        import json
        capability_levels_json = json.dumps(new_capability_levels)
        if params.score >= 80:
            # 高质量报告，增加完成计数
            completed_tasks = agent.completed_tasks + 1
            store.update_agent(
                report.agent_id,
                reputation=new_reputation,
                capability_levels=capability_levels_json,
                completed_tasks=completed_tasks
            )
        elif params.score < 60:
            # 低质量报告，增加失败计数
            failed_tasks = agent.failed_tasks + 1
            store.update_agent(
                report.agent_id,
                reputation=new_reputation,
                capability_levels=capability_levels_json,
                failed_tasks=failed_tasks
            )
        else:
            # 中等质量报告，只更新声望和能力
            store.update_agent(
                report.agent_id,
                reputation=new_reputation,
                capability_levels=capability_levels_json
            )
        
        return {
            "success": True,
            "report_id": params.report_id,
            "agent_id": report.agent_id,
            "new_reputation": new_reputation,
            "capability_updates": new_capability_levels,
            "score": params.score,
            "reputation_change": params.reputation_change
        }
    
    return {"success": False, "error": "评价失败"}


async def task_archive(params: TaskArchiveParams) -> Dict[str, Any]:
    """
    任务归档
    
    将已完成的任务标记为已归档状态。只有已评价的任务才能被归档。
    
    Args:
        params: 包含要归档的任务ID
        
    Returns:
        归档结果，包含成功状态
    """
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}
    
    if task.status != "completed":
        return {"success": False, "error": "任务未完成，无法归档"}
    
    if not task.evaluation:
        return {"success": False, "error": "任务未评价，无法归档"}
    
    if task.is_archived:
        return {"success": False, "error": "任务已归档"}
    
    success = store.update_task(
        params.task_id,
        is_archived=True,
        updated_at=datetime.utcnow().isoformat()
    )
    
    if success:
        return {
            "success": True,
            "task_id": params.task_id,
            "message": "任务已成功归档"
        }
    
    return {"success": False, "error": "归档失败"}


async def task_publish(params: TaskPublishParams) -> Dict[str, Any]:
    """
    创建新任务

    创建一个新的任务并添加到任务队列中。

    Args:
        params: 包含任务名称、详情、所需能力和依赖关系

    Returns:
        创建结果，包含任务ID和任务信息
    """
    task_id = IDGenerator.generate_task_id()

    task = Task(
        id=task_id,
        name=params.name,
        details=params.details,
        capability=params.capability,
        depends_on=params.depends_on,
        parent_task_id=params.parent_task_id if hasattr(params, 'parent_task_id') else None,
        created_by=params.created_by,
        candidates=params.candidates
    )
    success = store.save_task(task)

    if success:
        return {
        "success": True,
        "task_id": task_id,
        "task": task.model_dump()
    }
    else:
        return {"success": False, "error": "创建任务失败"}


async def task_delete(params: TaskDeleteParams) -> Dict[str, Any]:
    """
    删除任务

    删除一个任务，可以选择是否强制删除（即使有依赖关系）。
    如果任务被认领或已完成，也可以删除。

    Args:
        params: 包含task_id和force标志

    Returns:
        删除结果，包含成功状态和相关信息
    """
    task = store.get_task(params.task_id)
    if not task:
        return {"success": False, "error": "任务不存在"}

    # 检查是否有其他任务依赖此任务
    if not params.force:
        all_tasks = store.list_tasks()
        dependent_tasks = []
        
        for t in all_tasks:
            if params.task_id in t.depends_on:
                dependent_tasks.append(t.id)
        
        if dependent_tasks:
            return {
                "success": False,
                "error": f"任务被其他任务依赖，无法删除。依赖任务: {dependent_tasks}",
                "dependent_tasks": dependent_tasks
            }

    # 如果任务被认领，从代理的当前任务中移除
    if task.assignee and task.status == "claimed":
        agent = store.get_agent(task.assignee)
        if agent and params.task_id in agent.current_tasks:
            agent.current_tasks.remove(params.task_id)
            store.update_agent(task.assignee, current_tasks=agent.current_tasks)

    # 删除任务
    success = store.delete_task(params.task_id)
    
    if success:
        return {
            "success": True,
            "task_id": params.task_id,
            "message": "任务已成功删除"
        }
    else:
        return {"success": False, "error": "归档失败"}


async def task_suggest_agents(params: TaskSuggestParams) -> Dict[str, Any]:
    """
    为代理推荐最匹配的任务
    
    基于代理的能力和声望，从所有可用任务中筛选出最匹配的任务列表。
    优先返回代理具备能力且声望要求匹配的任务。
    
    Args:
        params: 包含agent_id和返回数量限制
        
    Returns:
        推荐的任务列表，按匹配度排序
    """
    agent = store.get_agent(params.agent_id)
    if not agent:
        return {"success": False, "error": "代理不存在"}
    
    # 获取所有待处理任务
    all_tasks = []
    for task_id in store.get_all_task_ids():
        task = store.get_task(task_id)
        if task and task.status == "pending":
            all_tasks.append(task)
    
    if not all_tasks:
        return {"success": True, "tasks": [], "message": "当前没有可用任务"}
    
    # 计算每个任务的匹配分数
    scored_tasks = []
    for task in all_tasks:
        # 检查代理是否具备所需能力
        if task.capability and task.capability not in agent.capabilities:
            continue
            
        # 检查依赖任务是否已完成
        if task.depends_on:
            all_deps_completed = True
            for dep_id in task.depends_on:
                dep_task = store.get_task(dep_id)
                if not dep_task or dep_task.status != "completed":
                    all_deps_completed = False
                    break
            if not all_deps_completed:
                continue
        
        # 检查租约是否过期
        now = datetime.utcnow()
        if task.lease_expires_at and task.lease_expires_at > now:
            continue
            
        # 计算匹配分数：基于能力等级和声望
        score = 0
        
        # 能力匹配加分
        capability_level = agent.capability_levels.get(task.capability, 1)
        score += capability_level * 10
        
        # 声望加分
        score += min(agent.reputation, 100)
        
        # 候选者优先级加分
        if params.agent_id in task.candidates:
            score += 50
            
        # 任务创建时间加分（越早创建的任务分数越高）
        days_since_creation = (now - task.created_at).days
        score += max(0, 30 - days_since_creation)
        
        scored_tasks.append({
            "task": task.model_dump(),
            "score": score,
            "is_candidate": params.agent_id in task.candidates
        })
    
    # 按分数排序，返回前limit个任务
    scored_tasks.sort(key=lambda x: x["score"], reverse=True)
    top_tasks = scored_tasks[:params.limit]
    
    return {
        "success": True,
        "tasks": top_tasks,
        "total_available": len(scored_tasks)
    }


async def agent_register(params: AgentRegisterParams) -> Dict[str, Any]:
    """
    代理注册
    
    新代理首次进入系统时的注册功能，用于声明代理的基本信息和能力。
    如果代理已存在，则更新其能力信息。
    
    Args:
        params: 包含代理ID、名称、能力列表和能力等级映射
        
    Returns:
        注册结果，包含成功状态和代理信息
    """
    # 强制从环境变量获取Agent ID和Name
    agent_id = os.getenv('AGENT_ID')
    if not agent_id:
        return {"success": False, "error": "环境变量AGENT_ID未设置"}
    
    name = os.getenv('AGENT_NAME')
    if not name:
        return {"success": False, "error": "环境变量AGENT_NAME未设置"}
    
    # 检查代理是否已存在
    existing_agent = store.get_agent(agent_id)
    
    if existing_agent:
        # 更新现有代理的能力信息（不更新声誉值）
        updates = {
            "name": name,
            "capabilities": params.capabilities,
            "capability_levels": params.capability_levels,
            "updated_at": datetime.utcnow().isoformat()
        }
        success = store.update_agent(agent_id, **updates)
        
        if success:
            updated_agent = store.get_agent(agent_id)
            return {
                "success": True,
                "agent_id": agent_id,
                "message": "代理信息已更新",
                "agent": updated_agent.model_dump(),
                "is_new": False
            }
        else:
            return {"success": False, "error": "更新代理信息失败"}
    
    # 创建新代理
    agent = Agent(
        id=agent_id,
        name=name,
        capabilities=params.capabilities,
        capability_levels=params.capability_levels,
        reputation=0,  # 新代理初始声望为0
        status="active",
        current_tasks=[],
        completed_tasks=0,
        failed_tasks=0
    )
    
    success = store.save_agent(agent)
    
    if success:
        return {
            "success": True,
            "agent_id": agent_id,
            "message": "代理注册成功",
            "agent": agent.model_dump(),
            "is_new": True
        }
    else:
        return {"success": False, "error": "代理注册失败"}


# 工具注册映射
async def report_list(params: ReportListParams) -> Dict[str, Any]:
    """
    获取报告列表
    
    根据提供的过滤条件返回报告列表。支持按任务ID、代理ID和状态筛选。
    
    Args:
        params: 包含过滤条件的参数对象
        
    Returns:
        包含报告列表的结果字典
    """
    try:
        reports = store.list_reports(
            task_id=params.task_id,
            agent_id=params.agent_id,
            status=params.status,
            limit=params.limit
        )
        
        return {
            "success": True,
            "reports": [report.dict() for report in reports]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"获取报告列表失败: {str(e)}"
        }


taskhub_tools = {
    "task_list": task_list,
    "task_claim": task_claim,
    "report_submit": report_submit,
    "report_list": report_list,
    "task_publish": task_publish,
    "task_delete": task_delete,
    "report_evaluate": report_evaluate,
    "task_archive": task_archive,
    "task_suggest_agents": task_suggest_agents,
    "agent_register": agent_register
}