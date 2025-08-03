"""
Core Taskhub API logic
"""

import logging
from datetime import datetime, timedelta, timezone

from ..models.hunter import Hunter
from ..models.knowledge import KnowledgeItem
from ..models.report import Report, ReportEvaluation
from ..models.task import Task, TaskStatus
from ..storage.sqlite_store import SQLiteStore
from ..utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def task_publish(
    store: SQLiteStore,
    name: str,
    details: str,
    required_skill: str,
    created_by: str,
    depends_on: list[str] | None = None,
) -> Task:
    task = Task(
        id=generate_id("task"),
        name=name,
        details=details,
        required_skill=required_skill,
        created_by=created_by,
        depends_on=depends_on or [],
        status=TaskStatus.PENDING,
    )
    await store.save_task(task)
    return task


async def task_claim(store: SQLiteStore, task_id: str, hunter_id: str) -> Task:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.status != TaskStatus.PENDING:
        raise ValueError(f"Task {task_id} is not pending, current status: {task.status}")

    hunter = await store.get_hunter(hunter_id)
    if not hunter or task.required_skill not in hunter.skills:
        raise ValueError(f"Hunter {hunter_id} does not possess the required skill: {task.required_skill}")

    task.status = TaskStatus.CLAIMED
    task.hunter_id = hunter_id
    task.lease_id = generate_id("lease")
    task.lease_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    return task


async def report_submit(
    store: SQLiteStore,
    task_id: str,
    hunter_id: str,
    status: str,
    result: str,
    details: str | None = None,
) -> Report:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.hunter_id != hunter_id:
        raise ValueError(f"Hunter {hunter_id} is not assigned to task {task_id}")

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
    return report


async def task_list(
    store: SQLiteStore,
    status: TaskStatus | None = None,
    required_skill: str | None = None,
    hunter_id: str | None = None,
) -> list[Task]:
    return await store.list_tasks(status.value if status else None, required_skill, hunter_id)


async def task_delete(store: SQLiteStore, task_id: str, force: bool = False) -> bool:
    task = await store.get_task(task_id)
    if not task:
        return True
    if not force and task.status == TaskStatus.CLAIMED:
        raise ValueError("Cannot delete a claimed task without force flag.")
    await store.delete_task(task_id)
    return True


async def report_evaluate(
    store: SQLiteStore,
    report_id: str,
    score: float,
    feedback: str,
    skill_updates: dict[str, int] | None = None,
) -> Report:
    report = await store.get_report(report_id)
    if not report:
        raise ValueError(f"Report not found: {report_id}")

    evaluation = ReportEvaluation(
        score=int(score),
        feedback=feedback,
        evaluator_id="admin",
        skill_updates=skill_updates or {},
    )
    report.evaluation = evaluation
    report.updated_at = datetime.now(timezone.utc)
    await store.save_report(report)

    hunter = await store.get_hunter(report.hunter_id)
    if hunter:
        for skill, change in evaluation.skill_updates.items():
            hunter.skills[skill] = hunter.skills.get(skill, 0) + change
        hunter.updated_at = datetime.now(timezone.utc)
        await store.save_hunter(hunter)

    return report


async def task_archive(store: SQLiteStore, task_id: str) -> Task:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    task.is_archived = True
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    return task


async def hunter_register(
    store: SQLiteStore,
    hunter_id: str,
    skills: dict[str, int] | None = None,
) -> Hunter:
    hunter = Hunter(
        id=hunter_id,
        skills=skills or {},
    )
    await store.save_hunter(hunter)
    return hunter


async def hunter_study(store: SQLiteStore, hunter_id: str, knowledge_id: str) -> Hunter:
    hunter = await store.get_hunter(hunter_id)
    knowledge = await store.get_knowledge_item(knowledge_id)
    if not hunter or not knowledge:
        raise ValueError("Hunter or KnowledgeItem not found.")

    for skill_tag in knowledge.skill_tags:
        hunter.skills[skill_tag] = hunter.skills.get(skill_tag, 0) + 10  # Study bonus

    hunter.updated_at = datetime.now(timezone.utc)
    await store.save_hunter(hunter)
    return hunter


async def knowledge_add(
    store: SQLiteStore,
    title: str,
    content: str,
    source: str,
    skill_tags: list[str],
    created_by: str,
) -> KnowledgeItem:
    item = KnowledgeItem(
        id=generate_id("kn"),
        title=title,
        content=content,
        source=source,
        skill_tags=skill_tags,
        created_by=created_by,
    )
    await store.save_knowledge_item(item)
    return item


async def knowledge_search(store: SQLiteStore, query: str, limit: int = 20) -> list[KnowledgeItem]:
    return await store.search_knowledge_items(query, limit)


async def hunter_list(store: SQLiteStore) -> list[Hunter]:
    return await store.list_hunters()


async def knowledge_list(store: SQLiteStore) -> list[KnowledgeItem]:
    return await store.list_knowledge_items()


async def report_list(store: SQLiteStore) -> list[Report]:
    return await store.list_reports()


async def get_system_guide() -> str:
    try:
        guide_path = "docs/Taskhub Guide.md"
        with open(guide_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.error("Could not find the Taskhub Guide at docs/Taskhub Guide.md")
        return "Error: System guide not found. Please contact an administrator."
    except Exception as e:
        logger.error(f"An error occurred while reading the system guide: {e}")
        return "Error: Could not retrieve the system guide due to an internal error."
