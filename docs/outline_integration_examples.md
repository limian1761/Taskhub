# Outline API 集成示例

## 在Taskhub中的实际应用

### 1. 基本客户端配置

```python
# src/taskhub/sdk/outline_client.py 中的使用示例
import httpx
from typing import Dict, Any, Optional
import os

class OutlineClient:
    def __init__(self, base_url: str = None, api_key: str = None):
        self.base_url = base_url or os.getenv('OUTLINE_BASE_URL', 'http://localhost:3000')
        self.api_key = api_key or os.getenv('OUTLINE_API_KEY')
        
        if not self.base_url or not self.api_key:
            raise ValueError("OUTLINE_BASE_URL and OUTLINE_API_KEY must be provided")
    
    async def _make_request(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """发送API请求的通用方法"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/{method}",
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
```

### 2. 文档管理示例

#### 创建文档
```python
async def create_knowledge_document(
    client: OutlineClient,
    title: str,
    content: str,
    collection_id: str = None
) -> Dict[str, Any]:
    """创建知识库文档"""
    
    payload = {
        "title": title,
        "text": content,
        "publish": True
    }
    
    if collection_id:
        payload["collectionId"] = collection_id
    
    result = await client._make_request("documents.create", payload)
    return result["data"]

# 使用示例
doc = await create_knowledge_document(
    client,
    title="Python异步编程指南",
    content="# Python异步编程\n\nasync/await是Python中处理异步操作的核心语法...",
    collection_id="collection-uuid-here"
)
```

#### 搜索文档
```python
async def search_knowledge_base(
    client: OutlineClient,
    query: str,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """搜索知识库"""
    
    payload = {
        "query": query,
        "limit": limit
    }
    
    result = await client._make_request("documents.search", payload)
    return result["data"]

# 使用示例
results = await search_knowledge_base(client, "Python async", limit=5)
for doc in results:
    print(f"{doc['title']} - {doc['url']}")
```

### 3. 集合管理示例

#### 创建知识库集合
```python
async def create_knowledge_collection(
    client: OutlineClient,
    name: str,
    description: str = "",
    color: str = "#4CAF50"
) -> Dict[str, Any]:
    """创建知识库集合"""
    
    payload = {
        "name": name,
        "description": description,
        "color": color,
        "permission": "read_write"
    }
    
    result = await client._make_request("collections.create", payload)
    return result["data"]

# 使用示例
python_collection = await create_knowledge_collection(
    client,
    name="Python开发",
    description="Python编程相关知识",
    color="#3776ab"
)
```

#### 获取所有集合
```python
async def get_all_collections(
    client: OutlineClient
) -> List[Dict[str, Any]]:
    """获取所有知识库集合"""
    
    payload = {}
    result = await client._make_request("collections.list", payload)
    return result["data"]
```

### 4. 错误处理最佳实践

```python
import asyncio
from typing import Optional

class KnowledgeService:
    def __init__(self, client: OutlineClient):
        self.client = client
    
    async def safe_create_document(
        self,
        title: str,
        content: str,
        collection_id: str = None,
        max_retries: int = 3
    ) -> Optional[Dict[str, Any]]:
        """安全创建文档，包含重试机制"""
        
        for attempt in range(max_retries):
            try:
                return await create_knowledge_document(
                    self.client, title, content, collection_id
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    # 速率限制，等待后重试
                    retry_after = int(e.response.headers.get('Retry-After', 5))
                    await asyncio.sleep(retry_after)
                else:
                    # 其他错误，直接抛出
                    raise
            except Exception as e:
                if attempt == max_retries - 1:
                    # 最后一次尝试失败
                    print(f"创建文档失败: {e}")
                    return None
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        return None
```

### 5. 批量操作示例

```python
async def batch_import_knowledge(
    client: OutlineClient,
    documents: List[Dict[str, str]],
    collection_id: str
) -> List[Dict[str, Any]]:
    """批量导入知识文档"""
    
    results = []
    for doc in documents:
        try:
            result = await create_knowledge_document(
                client,
                title=doc["title"],
                content=doc["content"],
                collection_id=collection_id
            )
            results.append(result)
            
            # 避免速率限制
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"导入文档失败 {doc['title']}: {e}")
            results.append(None)
    
    return results

# 使用示例
documents = [
    {"title": "Python基础", "content": "# Python基础教程\n\nPython是一种解释型语言..."},
    {"title": "Python高级特性", "content": "# 高级特性\n\n装饰器、生成器..."}
]

results = await batch_import_knowledge(client, documents, python_collection["id"])
```

### 6. 集成到Taskhub工作流

#### 知识收集任务
```python
async def collect_and_store_knowledge(
    task_result: Dict[str, Any],
    client: OutlineClient
) -> bool:
    """将任务结果存储到知识库"""
    
    # 1. 创建或获取对应的集合
    collection_name = task_result.get("domain", "General")
    collections = await get_all_collections(client)
    
    collection = next(
        (c for c in collections if c["name"] == collection_name),
        None
    )
    
    if not collection:
        collection = await create_knowledge_collection(
            client, collection_name, f"{collection_name}相关知识"
        )
    
    # 2. 创建文档
    title = f"{task_result['title']} - {task_result['timestamp']}"
    content = f"""
# {task_result['title']}

**收集时间**: {task_result['timestamp']}
**来源**: {task_result.get('source', 'Taskhub')}

## 内容
{task_result['content']}

## 标签
{', '.join(task_result.get('tags', []))}
    """
    
    doc = await create_knowledge_document(
        client, title, content, collection["id"]
    )
    
    return doc is not None
```

### 7. 监控和日志

```python
import logging
from datetime import datetime

class KnowledgeMonitor:
    def __init__(self, client: OutlineClient):
        self.client = client
        self.logger = logging.getLogger(__name__)
    
    async def sync_knowledge_stats(self) -> Dict[str, int]:
        """同步知识库统计信息"""
        
        try:
            # 获取所有集合
            collections = await get_all_collections(self.client)
            
            # 获取所有文档
            all_docs = []
            for collection in collections:
                docs = await self.client._make_request(
                    "documents.list", 
                    {"collectionId": collection["id"]}
                )
                all_docs.extend(docs["data"])
            
            stats = {
                "collections": len(collections),
                "documents": len(all_docs),
                "last_sync": datetime.now().isoformat()
            }
            
            self.logger.info(f"知识库同步完成: {stats}")
            return stats
            
        except Exception as e:
            self.logger.error(f"知识库同步失败: {e}")
            return {}
```

### 8. 配置管理

```python
# config.py 中的配置示例
from pydantic import BaseSettings

class OutlineConfig(BaseSettings):
    outline_base_url: str = "http://localhost:3000"
    outline_api_key: str = None
    outline_timeout: int = 30
    outline_max_retries: int = 3
    outline_rate_limit_delay: float = 1.0
    
    class Config:
        env_file = ".env"

# .env 文件示例
OUTLINE_BASE_URL=http://localhost:3000
OUTLINE_API_KEY=your_api_key_here
OUTLINE_TIMEOUT=30
OUTLINE_MAX_RETRIES=3
```

## 测试示例

```python
# 测试代码示例
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_knowledge_document():
    mock_client = AsyncMock()
    mock_client._make_request.return_value = {
        "data": {"id": "test-doc-id", "title": "Test Document"}
    }
    
    result = await create_knowledge_document(
        mock_client, "Test", "Content", "collection-id"
    )
    
    assert result["title"] == "Test Document"
    mock_client._make_request.assert_called_once()
```

这些示例展示了如何在Taskhub项目中有效地集成和使用Outline API，包括错误处理、批量操作、监控等关键方面。