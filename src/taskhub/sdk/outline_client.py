"""
Enhanced Outline API Client for Taskhub
基于Outline官方API文档的完整客户端实现
"""

import httpx
from typing import List, Dict, Any, Optional

from ..utils.config import config

BASE_URL = config.config["outline"]["url"]
API_KEY = config.config["outline"]["api_key"]

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


async def search_documents(query: str) -> List[Dict[str, Any]]:
    """Search for documents in Outline"""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.search",
            headers=HEADERS,
            json={"query": query}
        )
        response.raise_for_status()
        # Return data structure according to Outline API documentation
        return response.json().get("data", [])


async def create_document(title: str, content: str, collection_id: str, parent_document_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new document in Outline"""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.create",
            headers=HEADERS,
            data={
                "title": title,
                "text": content,
                "collectionId": collection_id,
                "parentDocumentId": parent_document_id,
            }
        )
        response.raise_for_status()
        return response.json().get("data", {})


async def get_document(document_id: str) -> Dict[str, Any]:
    """Get a document by ID from Outline"""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.info",
            headers=HEADERS,
            data={"id": document_id}
        )
        response.raise_for_status()
        return response.json().get("data", {})


async def list_documents(collection_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """List documents in a specific collection in Outline"""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.list",
            headers=HEADERS,
            json={"collectionId": collection_id, "limit": limit}
        )
        response.raise_for_status()
        return response.json().get("data", [])


async def delete_document(document_id: str) -> bool:
    """Delete a document by ID from Outline"""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.delete",
            headers=HEADERS,
            data={"id": document_id}
        )
        response.raise_for_status()
        return response.json().get("success", False)


async def answer_question(document_id: str, query: str) -> Dict[str, Any]:
    """Ask a question about a specific document and get an AI-generated answer."""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.answerQuestion",
            headers=HEADERS,
            json={"id": document_id, "query": query}
        )
        response.raise_for_status()
        return response.json().get("data", {})


async def update_document(document_id: str, title: Optional[str] = None, text: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing document in Outline."""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    payload = {"id": document_id}
    if title:
        payload["title"] = title
    if text:
        payload["text"] = text

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/documents.update",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return response.json().get("data", {})


async def list_collections(limit: int = 50) -> List[Dict[str, Any]]:
    """List all collections in Outline."""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/collections.list",
            headers=HEADERS,
            data={"limit": limit}
        )
        response.raise_for_status()
        return response.json().get("data", [])


async def create_collection(name: str, description: Optional[str] = None, color: Optional[str] = None) -> Dict[str, Any]:
    """Create a new collection in Outline."""
    if not BASE_URL or not API_KEY:
        raise ValueError("Outline URL and API key must be configured")

    payload = {"name": name}
    if description:
        payload["description"] = description
    if color:
        payload["color"] = color

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/api/collections.create",
            headers=HEADERS,
            json=payload
        )
        response.raise_for_status()
        return response.json().get("data", {})


# Add more functions as needed for full Outline API integration