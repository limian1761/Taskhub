"""
Report-related service functions for the Taskhub system.
"""

import logging
from datetime import datetime, timezone

from taskhub.models.hunter import Hunter
from taskhub.models.report import Report, ReportEvaluation
from taskhub.models.task import Task, TaskStatus
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id
from .task_service import task_publish

logger = logging.getLogger(__name__)


async def report_submit(
    store: SQLiteStore,
    task_id: str,
    hunter_id: str,
    status: str,
    result: str | None = None,
    details: str | None = None,
) -> Report:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.hunter_id != hunter_id:
        raise ValueError(f"Task {task_id} is not claimed by hunter {hunter_id}")

    report = Report(
        id=generate_id("report"),
        task_id=task_id,
        hunter_id=hunter_id,
        status=status,
        result=result,
        details=details,
    )
    await store.save_report(report)

    task.status = TaskStatus(status)
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    
    # Automatically create an evaluation task if the completed task was a NORMAL one
    if task.task_type == "NORMAL":
        evaluation_task_name = f"评价报告 {report.id[:8]}"
        evaluation_task = await task_publish(
            store,
            name=evaluation_task_name,
            details="请对附件中的报告进行评价和打分。",
            required_skill="report_evaluation",
            publisher_id="system", # Evaluation tasks are published by the system
            depends_on=[]
        )
        
        # Update task type and link the report
        evaluation_task.task_type = "EVALUATION"
        evaluation_task.report_id = report.id
        await store.save_task(evaluation_task)
    
    return report


async def report_evaluate(
    store: SQLiteStore,
    report_id: str,
    evaluator_id: str,
    score: int,
    feedback: str,
    skill_updates: dict[str, int] | None = None,
) -> Report:
    report = await store.get_report(report_id)
    if not report:
        raise ValueError(f"Report not found: {report_id}")

    # Rule: A hunter cannot evaluate their own report
    if report.hunter_id == evaluator_id:
        raise ValueError("A hunter cannot evaluate their own report.")

    evaluation = ReportEvaluation(
        id=generate_id("eval"),
        report_id=report_id,
        score=score,
        feedback=feedback,
        skill_updates=skill_updates or {},
        evaluator_id=evaluator_id,
    )
    await store.save_evaluation(evaluation)

    report.evaluation = evaluation
    await store.save_report(report)

    # Update hunter's skills and reputation based on evaluation and task priority
    task = await store.get_task(report.task_id)
    if not task:
        logger.warning(f"Task {report.task_id} not found for evaluated report {report.id}")
        return report

    hunter = await store.get_hunter(report.hunter_id)
    if not hunter:
        logger.warning(f"Hunter {report.hunter_id} not found for evaluated report {report.id}")
        return report

    # Calculate reputation and skill gain, boosted by task priority
    priority_bonus = 1 + (task.priority / 100.0)
    reputation_gain = int((score / 10) * priority_bonus) # Base gain is score/10
    hunter.reputation += reputation_gain

    if skill_updates:
        for skill, increment in skill_updates.items():
            skill_gain = int(increment * priority_bonus)
            hunter.skills[skill] = hunter.skills.get(skill, 0) + skill_gain
    
    await store.save_hunter(hunter)
    
    # 检查特性开关和评价分数
    from taskhub.utils.config import config
    if config.get("features.auto_generate_knowledge", True) and score >= 90:
        from . import llm_service, knowledge_service
        from taskhub.models.knowledge import KnowledgeStatus
        
        if task:
            # 1. 调用LLM服务生成知识
            title, content = await llm_service.summarize_task_for_knowledge(
                task.details, report.result
            )

            # 2. 创建草稿状态的知识条目
            await knowledge_service.knowledge_add(
                store=store,
                knowledge_id=f"knowledge_{report.id}",
                title=title,
                content=content,
                source=f"Auto-generated from task {task.id}",
                skill_tags=[task.required_skill],
                created_by="system_automata",
                status=KnowledgeStatus.DRAFT  # 明确指定为草稿
            )
            logger.info(f"Knowledge draft created automatically from task {task.id}")

    return report


async def report_list(store: SQLiteStore, task_id: str | None = None, hunter_id: str | None = None, status: str | None = None) -> list[Report]:
    """List reports with optional filtering.
    
    Args:
        store: The database store
        task_id: Optional task ID to filter by
        hunter_id: Optional hunter ID to filter by
        status: Optional status to filter by
        
    Returns:
        List of Report objects matching the criteria
    """
    return await store.list_reports(task_id, hunter_id, status)


async def delete_all_reports(store: SQLiteStore) -> None:
    """Delete all reports from the database."""
    await store.delete_all_reports()
    logger.info("All reports deleted from the database")


async def delete_report(store: SQLiteStore, report_id: str) -> None:
    """Delete a report from the database."""
    await store.delete_report(report_id)
    logger.info(f"Report {report_id} deleted from the database")
