"""
Knowledge-related service functions for the Taskhub system.
All knowledge is now managed directly in Outline.
"""

import logging
from typing import List, Dict, Any

from taskhub.sdk.outline_client import (
    create_document,
    search_documents,
    get_document,
    list_documents,
    delete_document,
    answer_question,
    update_document,
)
from taskhub.utils.config import config

logger = logging.getLogger(__name__)


async def knowledge_add(collection_id: str, title: str, content: str, parent_document_id: str = None) -> Dict[str, Any]:
    """
    Add a new knowledge item by creating a document in Outline.

    Args:
        collection_id: The ID of the collection to add the document to.
        title: The title of the knowledge item.
        content: The content of the knowledge item.
        parent_document_id: Optional ID of a parent document for nesting.

    Returns:
        The created document data from Outline.
    """
    if not collection_id:
        raise ValueError("Outline Collection ID must be provided.")

    logger.info(f"Creating document in Outline collection {collection_id} with title: {title}")
    outline_doc = await create_document(
        title=title,
        content=content,
        collection_id=collection_id,
        parent_document_id=parent_document_id,
    )
    logger.info(f"Successfully created document {outline_doc.get('id')} in Outline.")
    return outline_doc


async def knowledge_search(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Search for documents directly in Outline.

    Args:
        query: The search query.
        limit: Maximum number of results to return.

    Returns:
        List of search results from Outline.
    """
    logger.info(f"Searching Outline for: {query}")
    search_results = await search_documents(query)
    return search_results[:limit]


async def knowledge_list(collection_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    List all knowledge items from a specific Outline collection.

    Args:
        collection_id: The ID of the collection to list documents from.
        limit: The maximum number of documents to return.

    Returns:
        List of document data from Outline.
    """
    logger.info(f"Listing documents from Outline collection {collection_id}")
    return await list_documents(collection_id=collection_id, limit=limit)


async def knowledge_get(document_id: str) -> Dict[str, Any]:
    """
    Get a specific knowledge item by its Outline document ID.

    Args:
        document_id: The document ID from Outline.

    Returns:
        The requested document data from Outline.
    """
    logger.info(f"Fetching document {document_id} from Outline.")
    return await get_document(document_id)


async def knowledge_delete(document_id: str) -> bool:
    """
    Delete a knowledge item by its Outline document ID.

    Args:
        document_id: The document ID from Outline to delete.

    Returns:
        True if deletion was successful, False otherwise.
    """
    logger.info(f"Deleting document {document_id} from Outline.")
    return await delete_document(document_id)


async def knowledge_answer_question(document_id: str, query: str) -> Dict[str, Any]:
    """
    Ask a question about a specific document in Outline.

    Args:
        document_id: The document ID from Outline.
        query: The question to ask about the document.

    Returns:
        The answer data from Outline.
    """
    logger.info(f"Asking question about document {document_id}: '{query}'")
    return await answer_question(document_id=document_id, query=query)


async def knowledge_update(document_id: str, title: str = None, content: str = None) -> Dict[str, Any]:
    """
    Updates an existing knowledge document in Outline.

    Args:
        document_id: The ID of the document to update.
        title: The new title for the document (optional).
        content: The new content for the document in Markdown format (optional).

    Returns:
        A dictionary representation of the updated Outline document.
    """
    logger.info(f"Updating document {document_id} in Outline.")
    return await update_document(document_id=document_id, title=title, content=content)
