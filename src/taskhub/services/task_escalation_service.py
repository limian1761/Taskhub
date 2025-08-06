"""
Task escalation service for the Taskhub system.
"""

import logging
from datetime import datetime, timedelta, timezone

from taskhub.storage.sqlite_store import SQLiteStore
from taskhub.utils.config import config

logger = logging.getLogger(__name__)


async def check_and_escalate_stale_tasks(store: SQLiteStore):
    """
    Scans for assigned tasks that have not been acted upon and escalates them.
    """
    from . import hunter_service  # 导入hunter_service
    
    logger.info("Running job: Checking for stale tasks...")
    
    timeout_hours = config.get("workflow.evaluation_task_timeout_hours", 24)
    stale_threshold = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
    
    # 1. 查询所有被指派但仍处于"待定"状态的过时任务
    all_tasks = await store.list_tasks(status="pending")
    stale_tasks = [
        task for task in all_tasks
        if task.assignee_id is not None and task.created_at < stale_threshold
    ]
    
    if not stale_tasks:
        logger.info("No stale tasks found.")
        return
    
    for task in stale_tasks:
        logger.warning(f"Task {task.id} assigned to {task.assignee_id} is stale. Escalating.")
        
        await store.begin()
        try:
            # 2. 尝试重新分配给下一个最佳人选
            new_hunter = await hunter_service.find_best_hunter_for_task(
                store,
                skill=task.required_skill,
                exclude_hunter_ids=[task.assignee_id]  # 排除当前指派的人
            )
            
            if new_hunter:
                # 3a. 如果找到新人选，则重新指派
                task.assignee_id = new_hunter.id
                logger.info(f"Task {task.id} has been re-assigned to {new_hunter.id}.")
            else:
                # 3b. 如果找不到其他人，则取消指派，并提升优先级，使其回到公共任务池
                task.assignee_id = None
                task.priority += 10  # 增加优先级以吸引注意
                logger.warning(f"No other hunters found for task {task.id}. Un-assigning and increasing priority.")
            
            task.updated_at = datetime.now(timezone.utc)
            await store.save_task(task)
            await store.commit()
            
        except Exception as e:
            logger.error(f"Failed to escalate task {task.id}. Rolling back. Error: {e}")
            await store.rollback()