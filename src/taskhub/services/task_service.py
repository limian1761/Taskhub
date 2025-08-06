"""
Task-related service functions for the Taskhub system.
"""

import logging
from datetime import datetime, timedelta, timezone

from taskhub.models.hunter import Hunter
from taskhub.models.task import Task, TaskStatus
from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.id_generator import generate_id

logger = logging.getLogger(__name__)


async def task_publish(
    store: SQLiteStore,
    name: str,
    details: str,
    required_skill: str,
    publisher_id: str,
    depends_on: list[str] | None = None,
    task_type: str = "NORMAL",  # 添加任务类型参数，默认为NORMAL
) -> Task:
    """Publish a new task.
    
    The task's priority is determined by the publisher's reputation.
    
    Args:
        store: The database store to save the task to.
        name: The name/title of the task.
        details: Detailed instructions for the task.
        required_skill: The skill required to complete this task.
        publisher_id: The ID of the hunter publishing the task.
        depends_on: Optional list of task IDs that must be completed before this task.
        task_type: The type of task (NORMAL, EVALUATION, or RESEARCH).
        
    Returns:
        The newly created Task object.
    """
    publisher = await store.get_hunter(publisher_id)
    if not publisher:
        raise ValueError(f"Publisher (hunter) with ID {publisher_id} not found.")

    # Calculate priority based on publisher's reputation
    priority = publisher.reputation // 10  # Example: 10 reputation points = 1 priority point

    task = Task(
        id=generate_id("task"),
        name=name,
        details=details,
        required_skill=required_skill,
        published_by_hunter_id=publisher_id,
        priority=priority,
        depends_on=depends_on or [],
        task_type=task_type,  # 设置任务类型
    )
    await store.save_task(task)
    return task


async def task_claim(store: SQLiteStore, task_id: str, hunter_id: str) -> Task:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.status != TaskStatus.PENDING:
        raise ValueError(f"Task {task_id} is not pending, current status: {task.status}")
    
    # Rule: A hunter cannot claim their own task
    if task.published_by_hunter_id == hunter_id:
        raise ValueError("A hunter cannot claim their own published task.")

    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter {hunter_id} not found.")
    if task.required_skill not in hunter.skills:
        raise ValueError(
            f"Hunter {hunter_id} does not possess the required skill: {task.required_skill}. "
            "Please learn this skill and re-register your skills with 0 skill points to start."
        )

    task.status = TaskStatus.CLAIMED
    task.hunter_id = hunter_id
    task.lease_id = generate_id("lease")
    task.lease_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    return task


async def task_start(store: SQLiteStore, task_id: str, hunter_id: str) -> Task:
    """Start working on a claimed task.
    
    Args:
        store: The database store.
        task_id: The ID of the task to start.
        hunter_id: The ID of the hunter starting the task.
        
    Returns:
        The updated task.
        
    Raises:
        ValueError: If the task is not found, not claimed by the hunter, or already started.
    """
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.hunter_id != hunter_id:
        raise ValueError(f"Task {task_id} is not claimed by hunter {hunter_id}")
    if task.status != TaskStatus.CLAIMED:
        raise ValueError(f"Task {task_id} is not claimed, current status: {task.status}")
    
    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    return task


async def task_complete(store: SQLiteStore, task_id: str, result: str, status: str, hunter_id: str) -> Task:
    """Complete a task.
    
    Args:
        store: The database store.
        task_id: The ID of the task to complete.
        result: The result of the task.
        status: The final status of the task.
        hunter_id: The ID of the hunter completing the task.
        
    Returns:
        The completed task.
        
    Raises:
        ValueError: If the task is not found, not claimed by the hunter, or not in progress.
    """
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.hunter_id != hunter_id:
        raise ValueError(f"Task {task_id} is not claimed by hunter {hunter_id}")
    if task.status != TaskStatus.IN_PROGRESS:
        raise ValueError(f"Task {task_id} is not in progress, current status: {task.status}")
    
    task.status = TaskStatus(status)
    task.result = result
    task.completed_at = datetime.now(timezone.utc)
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    
    # 确保评价任务完成后不会触发新任务
    # 对于非评价任务，可以在这里添加触发后续任务的逻辑
    # 但对于EVALUATION类型的任务，工作流到此结束
    
    return task


async def get_task(store: SQLiteStore, task_id: str) -> Task | None:
    """Get a task by ID.
    
    Args:
        store: The database store.
        task_id: The ID of the task to retrieve.
        
    Returns:
        The task if found, None otherwise.
    """
    return await store.get_task(task_id)


async def task_list(
    store: SQLiteStore,
    status: TaskStatus | None = None,
    required_skill: str | None = None,
    hunter_id: str | None = None,
) -> list[Task]:
    return await store.list_tasks(status.value if status else None, required_skill, hunter_id)


async def task_delete(store: SQLiteStore, task_id: str) -> None:
    """Delete a task from the system.
    
    Args:
        store: The database store
        task_id: The ID of the task to delete
    """
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")
    
    await store.delete_task(task_id)
    logger.info(f"Task {task_id} deleted")


async def delete_all_tasks(store: SQLiteStore) -> None:
    """Delete all tasks from the database."""
    await store.delete_all_tasks()
    logger.info("All tasks deleted from the database")


async def task_archive(store: SQLiteStore, task_id: str) -> Task:
    task = await store.get_task(task_id)
    if not task:
        raise ValueError(f"Task not found: {task_id}")
    if task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise ValueError(f"Task {task_id} must be completed or failed to be archived")

    task.status = TaskStatus.ARCHIVED
    task.updated_at = datetime.now(timezone.utc)
    await store.save_task(task)
    return task
