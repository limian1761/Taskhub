"""
System-level service functions for the Taskhub system.
"""

import logging
from pathlib import Path

from taskhub.models.hunter import Hunter
from taskhub.models.task import Task, TaskStatus
from taskhub.storage.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


import os
from pathlib import Path

async def get_system_guide() -> str:
    """
    返回实际的guide文档
    """
    try:
        # 假设README.md在项目根目录下
        readme_path = Path(__file__).parent.parent / "taskhub_guide.md"
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
        return "未找到taskhub_guide.md文件，请检查文件是否存在。"
    except Exception as e:
        return f"读取taskhub_guide.md文件时出错: {str(e)}"

async def get_system_stats(store: SQLiteStore) -> dict:
    """Get statistics for the entire system for the admin dashboard."""
    hunters = await store.list_hunters()
    tasks = await store.list_tasks()

    # Get active hunters (e.g., those assigned to a task in progress)
    in_progress_hunter_ids = {
        t.hunter_id for t in tasks if t.status == TaskStatus.IN_PROGRESS and t.hunter_id
    }
    active_hunters = len(in_progress_hunter_ids)

    stats = {
        "total_tasks": len(tasks),
        "in_progress": len(
            [t for t in tasks if t.status == TaskStatus.IN_PROGRESS]
        ),
        "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
        "active_hunters": active_hunters,
    }
    return stats


async def get_all_tasks(store: SQLiteStore) -> list[dict]:
    """Get a list of all tasks with essential details for the admin table."""
    tasks = await store.list_tasks()
    
    # Sort tasks by a reasonable default, e.g., status
    tasks.sort(key=lambda t: t.status.value)

    task_list = []
    for task in tasks:
        task_list.append(
            {
                "id": task.id,
                "name": task.name,
                "status": task.status.value,
                "assignee": task.hunter_id[:8] + "..." if task.hunter_id else "Unassigned",
            }
        )
    return task_list




async def list_hunters_with_details(store: SQLiteStore) -> list[Hunter]:
    """List all hunters with their full details."""
    return await store.list_hunters()


async def adjust_hunter_reputation(
    store: SQLiteStore, hunter_id: str, new_reputation: int
) -> Hunter:
    """Manually adjust a hunter's reputation."""
    hunter = await store.get_hunter(hunter_id)
    if not hunter:
        raise ValueError(f"Hunter with ID {hunter_id} not found.")

    hunter.reputation = new_reputation
    await store.save_hunter(hunter)
    logger.info(f"Admin adjusted reputation for hunter {hunter_id} to {new_reputation}")
    return hunter


async def get_task_with_details(store: SQLiteStore, task_id: str) -> dict | None:
    """Get a single task enriched with publisher and assignee details."""
    task = await store.get_task(task_id)
    if not task:
        return None

    task_dict = task.model_dump()

    if task.published_by_hunter_id:
        publisher = await store.get_hunter(task.published_by_hunter_id)
        task_dict["publisher_details"] = publisher.model_dump(
            include={"id", "reputation"}
        )

    if task.hunter_id:
        assignee = await store.get_hunter(task.hunter_id)
        task_dict["assignee_details"] = assignee.model_dump(
            include={"id", "skills", "reputation"}
        )

    return task_dict


async def check_and_escalate_stale_tasks(store: SQLiteStore) -> int:
    """
    检查并升级过期的任务。
    
    检查标准：
    - 处于IN_PROGRESS状态超过24小时未更新的任务
    - 标记为CLAIMED但超过12小时未开始处理的任务
    
    升级操作：
    - 将过期任务状态改为FAILED
    - 记录失败原因
    - 返回处理的任务数量
    
    Args:
        store: SQLiteStore实例
        
    Returns:
        int: 被升级的任务数量
    """
    from datetime import datetime, timedelta, timezone
    from taskhub.models.task import TaskStatus
    
    try:
        tasks = await store.list_tasks()
        stale_count = 0
        
        now = datetime.now(timezone.utc)
        
        for task in tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                # 检查是否超过24小时未更新
                if task.updated_at and (now - task.updated_at) > timedelta(hours=24):
                    logger.info(f"任务 {task.id} 超时24小时未更新，标记为失败")
                    task.status = TaskStatus.FAILED
                    task.updated_at = now
                    await store.save_task(task)
                    stale_count += 1
                    
            elif task.status == TaskStatus.CLAIMED:
                # 检查是否超过12小时未开始处理
                if task.updated_at and (now - task.updated_at) > timedelta(hours=12):
                    logger.info(f"任务 {task.id} 认领后12小时未开始，标记为失败")
                    task.status = TaskStatus.FAILED
                    task.updated_at = now
                    await store.save_task(task)
                    stale_count += 1
        
        if stale_count > 0:
            logger.info(f"成功升级 {stale_count} 个过期任务")
        
        return stale_count
        
    except Exception as e:
        logger.error(f"检查过期任务时发生错误: {e}")
        raise


async def get_task_interaction_graph(store: SQLiteStore) -> dict:
    """
    获取任务交互网络图所需的数据。
    节点: Hunters, Tasks
    边: Published, Claimed
    """
    hunters = await store.list_hunters()
    tasks = await store.list_tasks()

    nodes = []
    links = []

    # 创建猎人节点
    for hunter in hunters:
        nodes.append({
            "id": f"hunter-{hunter.id}",
            "name": f"Hunter {hunter.id[:4]}",
            "symbolSize": 10 + hunter.reputation / 10,  # 声望越高，节点越大
            "value": hunter.reputation,
            "category": 0  # 猎人分类
        })

    # 创建任务节点并建立连接
    for task in tasks:
        nodes.append({
            "id": f"task-{task.id}",
            "name": f"Task {task.name[:15]}",
            "symbolSize": 10 + task.priority, # 优先级越高，节点越大
            "value": task.priority,
            "category": 1  # 任务分类
        })
        
        # 创建 "发布了" 的连接
        if task.published_by_hunter_id:
            links.append({
                "source": f"hunter-{task.published_by_hunter_id}",
                "target": f"task-{task.id}",
                "name": "发布"
            })
            
        # 创建 "认领了" 的连接
        if task.hunter_id:
            links.append({
                "source": f"task-{task.id}",
                "target": f"hunter-{task.hunter_id}",
                "name": "认领"
            })

    # 定义分类
    categories = [
        {"name": "Hunter"},
        {"name": "Task"}
    ]

    return {"nodes": nodes, "links": links, "categories": categories}