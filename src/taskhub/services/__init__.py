"""
Taskhub services package.
"""

# Import all service functions for easy access
from .task_service import (
    task_publish,
    task_claim,
    task_start,
    task_complete,
    get_task,
    task_list,
    task_delete,
    task_archive,
)

from .hunter_service import (
    hunter_register,
    hunter_study,
    get_hunter,
    hunter_list,
)

from .knowledge_service import (
    knowledge_add,
    knowledge_search,
    knowledge_list,
)

from .report_service import (
    report_submit,
    report_evaluate,
    report_list,
)

from .system_service import (
    get_system_guide,
)

__all__ = [
    # Task services
    "task_publish",
    "task_claim",
    "task_start",
    "task_complete",
    "get_task",
    "task_list",
    "task_delete",
    "task_archive",
    
    # Hunter services
    "hunter_register",
    "hunter_study",
    "get_hunter",
    "hunter_list",
    
    # Knowledge services
    "knowledge_add",
    "knowledge_search",
    "knowledge_list",
    
    # Report services
    "report_submit",
    "report_evaluate",
    "report_list",
    
    # System services
    "get_system_guide",
]