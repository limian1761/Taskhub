"""
Domain Service for Taskhub.
Manages domains by mapping them to Outline Collections.
"""
import logging
from typing import List, Dict, Any, Optional

from taskhub.sdk.outline_client import list_collections, create_collection

logger = logging.getLogger(__name__)


async def list_domains() -> List[Dict[str, Any]]:
    """
    Lists all domains by fetching collections from Outline.

    Returns:
        A list of collections from Outline.
    """
    logger.info("Listing all domains (collections) from Outline.")
    return await list_collections()


async def create_domain(name: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new domain by creating a collection in Outline.

    Args:
        name: The name of the new domain/collection.
        description: A description for the new domain/collection.

    Returns:
        The newly created collection data from Outline.
    """
    logger.info(f"Creating new domain (collection) in Outline with name: {name}")
    return await create_collection(name=name, description=description)
