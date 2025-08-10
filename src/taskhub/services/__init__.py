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
    knowledge_list,
    knowledge_search,
)

from .domain_service import (
    create_domain,
    list_domains,
)

from .discussion_service import (
    post_message,
    get_unread_messages,
    mark_as_read,
    get_all_messages,
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
    "knowledge_list",
    "knowledge_search",

    # Domain services
    "create_domain",
    "list_domains",
    
    # Discussion service functions
    "post_message",
    "get_unread_messages",
    "mark_as_read",
    "get_all_messages",
    
    # Report services
    "report_submit",
    "report_evaluate",
    "report_list",
    
    # System services
    "get_system_guide",
]