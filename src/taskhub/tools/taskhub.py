import os
import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from ..models.task import Task
from ..models.agent import Agent
from ..models.report import Report, ReportEvaluation
from ..models.domain import Domain
from ..models.knowledge import KnowledgeItem
from ..storage.sqlite_store import SQLiteStore
from ..utils.id_generator import IDGenerator

# --- Domain Logic ---
async def create_domain(db: SQLiteStore, name: str, description: str) -> Domain:
    domain_id = IDGenerator.generate_domain_id()
    domain = Domain(id=domain_id, name=name, description=description)
    db.save_domain(domain)
    return domain

# --- Knowledge Logic ---
async def knowledge_add(db: SQLiteStore, title: str, content: str, source: str, domain_tags: List[str], created_by: str) -> KnowledgeItem:
    item_id = IDGenerator.generate_knowledge_id()
    item = KnowledgeItem(id=item_id, title=title, content=content, source=source, domain_tags=domain_tags, created_by=created_by)
    db.save_knowledge_item(item)
    return item

# --- Agent Logic ---
async def agent_study(db: SQLiteStore, agent_id: str, knowledge_id: str) -> Agent:
    agent = db.get_agent(agent_id)
    knowledge_item = db.get_knowledge_item(knowledge_id)
    if not agent or not knowledge_item:
        raise ValueError("Agent or Knowledge Item not found.")
    
    for domain_id in knowledge_item.domain_tags:
        agent.domain_scores[domain_id] = agent.domain_scores.get(domain_id, 0) + 1
    
    db.update_agent(agent_id, domain_scores=json.dumps(agent.domain_scores))
    return agent

async def agent_register(db: SQLiteStore, capabilities: List[str], domain_scores: Dict[str, int] = None) -> Agent:
    agent_id = os.environ.get("AGENT_ID")
    agent_name = os.environ.get("AGENT_NAME", f"Agent-{IDGenerator._generate_random_string(8)}")
    if not agent_id:
        raise ValueError("AGENT_ID environment variable not set")

    agent = db.get_agent(agent_id)
    now = datetime.utcnow()
    if agent:
        agent.capabilities = capabilities
        agent.domain_scores = domain_scores or agent.domain_scores
        agent.updated_at = now
    else:
        agent = Agent(id=agent_id, name=agent_name, capabilities=capabilities, domain_scores=domain_scores or {}, created_at=now, updated_at=now)
    db.save_agent(agent)
    return agent

# --- Task & Report Logic ---
async def list_tasks(db: SQLiteStore, status: Optional[str] = None, capability: Optional[str] = None, assignee: Optional[str] = None) -> List[Task]:
    return db.list_tasks(status=status, capability=capability, assignee=assignee)

async def get_task_by_id(db: SQLiteStore, task_id: str) -> Optional[Task]:
    return db.get_task(task_id)

async def list_reports(db: SQLiteStore, task_id: Optional[str] = None, agent_id: Optional[str] = None, status: Optional[str] = None, limit: int = 100) -> List[Report]:
    return db.list_reports(task_id=task_id, agent_id=agent_id, status=status, limit=limit)

async def get_report_by_id(db: SQLiteStore, report_id: str) -> Optional[Report]:
    return db.get_report(report_id)

async def task_publish(db: SQLiteStore, name: str, details: str, capability: str, depends_on: List[str] = None) -> Task:
    task_id = IDGenerator.generate_task_id()
    now = datetime.utcnow()
    task = Task(id=task_id, name=name, details=details, capability=capability, depends_on=depends_on or [], created_at=now, updated_at=now)
    db.save_task(task)
    return task

# ... (other functions)