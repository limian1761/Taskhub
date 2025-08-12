"""
Enhanced Outline API Client for Taskhub
基于官方OpenAPI规范的完整客户端实现
参考: https://github.com/outline/openapi
"""

import httpx
from typing import List, Dict, Any, Optional

from ..utils.config import config

BASE_URL = config.config["outline"]["url"].rstrip('/')
API_KEY = config.config["outline"]["api_key"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}


async def search_documents(query: str, limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
    """Search for documents in Outline
    
    Args:
        query: Search query string
        limit: Maximum number of results to return (default: 25)
        offset: Number of results to skip (default: 0)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.search",
            headers=HEADERS,
            json={
                "query": query,
                "limit": limit,
                "offset": offset
            }
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", [])


async def create_document(
    title: str, 
    content: str, 
    collection_id: str, 
    parent_document_id: Optional[str] = None,
    publish: bool = False
) -> Dict[str, Any]:
    """Create a new document in Outline
    
    Args:
        title: Document title
        content: Document content in Markdown format
        collection_id: Collection ID where document will be created
        parent_document_id: Parent document ID (optional)
        publish: Whether to immediately publish the document (default: False)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    payload = {
        "title": title,
        "text": content,
        "collectionId": collection_id,
        "publish": publish
    }
    
    if parent_document_id:
        payload["parentDocumentId"] = parent_document_id
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.create",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


async def get_document(document_id: str) -> Dict[str, Any]:
    """Get a document by ID from Outline
    
    Args:
        document_id: Document ID to retrieve
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.info",
            headers=HEADERS,
            json={"id": document_id}
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


async def list_documents(
    collection_id: Optional[str] = None, 
    limit: int = 25, 
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List documents in Outline
    
    Args:
        collection_id: Collection ID to filter documents (optional)
        limit: Maximum number of results to return (default: 25)
        offset: Number of results to skip (default: 0)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    payload = {
        "limit": limit,
        "offset": offset
    }
    
    if collection_id:
        payload["collectionId"] = collection_id
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.list",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", [])


async def delete_document(document_id: str) -> bool:
    """Delete a document by ID from Outline
    
    Args:
        document_id: Document ID to delete
    
    Returns:
        bool: True if deletion was successful
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.delete",
            headers=HEADERS,
            json={"id": document_id}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("ok", False) and data.get("success", False)


async def answer_question(document_id: str, query: str) -> Dict[str, Any]:
    """Ask a question about a specific document and get an AI-generated answer
    
    Args:
        document_id: Document ID to ask about
        query: Question to ask about the document
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.answer",
            headers=HEADERS,
            json={"id": document_id, "query": query}
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


async def update_document(
    document_id: str, 
    title: Optional[str] = None, 
    text: Optional[str] = None,
    publish: Optional[bool] = None
) -> Dict[str, Any]:
    """Update an existing document in Outline
    
    Args:
        document_id: Document ID to update
        title: New title (optional)
        text: New content in Markdown format (optional)
        publish: Whether to publish/unpublish the document (optional)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    payload = {"id": document_id}
    if title is not None:
        payload["title"] = title
    if text is not None:
        payload["text"] = text
    if publish is not None:
        payload["publish"] = publish

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.update",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


async def list_collections(limit: int = 25, offset: int = 0) -> List[Dict[str, Any]]:
    """List all collections in Outline
    
    Args:
        limit: Maximum number of results to return (default: 25)
        offset: Number of results to skip (default: 0)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/collections.list",
            headers=HEADERS,
            json={"limit": limit, "offset": offset}
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", [])


async def create_collection(
    name: str, 
    description: Optional[str] = None, 
    color: Optional[str] = None,
    permission: Optional[str] = None,
    sharing: Optional[bool] = None
) -> Dict[str, Any]:
    """Create a new collection in Outline
    
    Args:
        name: Collection name
        description: Collection description (optional)
        color: Collection color as hex code (optional)
        permission: Default permission level (optional: 'read', 'read_write')
        sharing: Whether sharing is enabled (optional)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    payload = {"name": name}
    if description:
        payload["description"] = description
    if color:
        payload["color"] = color
    if permission:
        payload["permission"] = permission
    if sharing is not None:
        payload["sharing"] = sharing

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/collections.create",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


async def get_collection(collection_id: str) -> Dict[str, Any]:
    """Get a collection by ID from Outline
    
    Args:
        collection_id: Collection ID to retrieve
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/collections.info",
            headers=HEADERS,
            json={"id": collection_id}
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})


# 新增辅助函数
async def move_document(document_id: str, collection_id: str, parent_document_id: Optional[str] = None) -> Dict[str, Any]:
    """Move a document to a different collection or parent
    
    Args:
        document_id: Document ID to move
        collection_id: Target collection ID
        parent_document_id: Target parent document ID (optional)
    """
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    payload = {
        "id": document_id,
        "collectionId": collection_id
    }
    
    if parent_document_id:
        payload["parentDocumentId"] = parent_document_id

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.move",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise Exception(f"API Error: {data.get('error', 'Unknown error')}")
        return data.get("data", {})