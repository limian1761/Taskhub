"""
Knowledge and Domain related tools for the Taskhub system,
interacting directly with Outline.
"""

import logging
from typing import Any, List, Dict, Optional

# Import the FastMCP instance from mcp_server
from .. import mcp

from taskhub.services import knowledge_service, domain_service
from taskhub.context import get_app_context
from taskhub.utils.error_handler import (
    handle_tool_errors,
    create_success_response,
    ValidationError,
    NotFoundError,
    validate_required_fields,
    validate_string_length
)

logger = logging.getLogger(__name__)

# --- Domain (Collection) Tools ---

@mcp.tool()
async def create_domain(name: str, description: str = None) -> Dict[str, Any]:
    """
    Creates a new skill domain by creating a Collection in Outline.

    Args:
        name: The name of the new domain/collection.
        description: An optional description for the domain/collection.

    Returns:
        A dictionary representation of the newly created Outline Collection.
    """
    logger.info(f"Creating new domain (collection): {name}")
    collection = await domain_service.create_domain(name=name, description=description)
    return collection

@mcp.tool()
async def list_domains() -> List[Dict[str, Any]]:
    """
    Lists all available skill domains by listing Collections from Outline.

    Returns:
        A list of dictionaries, each representing an Outline Collection.
    """
    logger.info("Listing all domains (collections).")
    collections = await domain_service.list_domains()
    return collections

# --- Knowledge (Document) Tools ---

@mcp.tool()
async def add_knowledge(collection_id: str, title: str, content: str, parent_document_id: str = None) -> Dict[str, Any]:
    """
    Adds a new knowledge document to a specific Collection in Outline.

    Args:
        collection_id: The ID of the collection (domain) to add the document to.
        title: The title of the document.
        content: The main content of the document in Markdown format.
        parent_document_id: Optional ID of a parent document for nesting.

    Returns:
        A dictionary representation of the newly created Outline document.
    """
    logger.info(f"Attempting to add knowledge '{title}' to collection {collection_id}")
    document = await knowledge_service.knowledge_add(
        collection_id=collection_id,
        title=title,
        content=content,
        parent_document_id=parent_document_id
    )
    logger.info(f"Successfully added knowledge {document.get('id')}")
    return document

@mcp.tool()
async def list_knowledge(collection_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Lists knowledge documents from a specific Collection in Outline.

    Args:
        collection_id: The ID of the collection (domain) to list documents from.
        limit: The maximum number of documents to return.

    Returns:
        A list of dictionaries, each representing an Outline document.
    """
    logger.info(f"Listing up to {limit} documents from collection {collection_id}.")
    documents = await knowledge_service.knowledge_list(collection_id=collection_id, limit=limit)
    return documents

@mcp.tool()
async def search_knowledge(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Searches for knowledge documents in the Outline knowledge base.

    Args:
        query: The search query string.
        limit: Maximum number of results to return.

    Returns:
        A list of search result objects from Outline.
    """
    logger.info(f"Searching knowledge for: {query}")
    results = await knowledge_service.knowledge_search(query=query, limit=limit)
    return results

@mcp.tool()
async def get_knowledge(document_id: str) -> Dict[str, Any]:
    """
    Retrieves a specific knowledge document from Outline by its ID.

    Args:
        document_id: The ID of the document to retrieve.

    Returns:
        A dictionary representation of the requested Outline document.
    """
    logger.info(f"Getting knowledge for document ID: {document_id}")
    document = await knowledge_service.knowledge_get(document_id=document_id)
    return document

@mcp.tool()
async def delete_knowledge(document_id: str) -> Dict[str, bool]:
    """
    Deletes a knowledge document from Outline by its ID.

    Args:
        document_id: The ID of the document to delete.

    Returns:
        A dictionary indicating whether the deletion was successful.
    """
    logger.info(f"Deleting knowledge document ID: {document_id}")
    success = await knowledge_service.knowledge_delete(document_id=document_id)
    return {"success": success}

@mcp.tool()
async def answer_question(document_id: str, question: str) -> Dict[str, Any]:
    """
    Asks a question about a specific document and gets an AI-generated answer.

    Args:
        document_id: The ID of the document to ask the question about.
        question: The specific question to ask.

    Returns:
        A dictionary containing the answer and related information from Outline.
    """
    logger.info(f"Asking question about document {document_id}: '{question}'")
    answer = await knowledge_service.knowledge_answer_question(
        document_id=document_id, query=question
    )
    return answer

@mcp.tool()
async def update_knowledge(document_id: str, title: str = None, content: str = None) -> Dict[str, Any]:
    """
    Updates an existing knowledge document in Outline.

    Args:
        document_id: The ID of the document to update.
        title: The new title for the document (optional).
        content: The new content for the document in Markdown format (optional).

    Returns:
        A dictionary representation of the updated Outline document.
    """
    if not title and not content:
        raise ValueError("Either 'title' or 'content' must be provided to update a document.")

    logger.info(f"Updating document {document_id}...")
    updated_document = await knowledge_service.knowledge_update(
        document_id=document_id, title=title, content=content
    )
    return updated_document

