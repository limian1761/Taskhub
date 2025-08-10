# 知识库集成指南

## 当前状态

由于Outline知识库服务暂时不可用（502 Bad Gateway），我们提供以下替代方案来连接和管理知识库：

## 临时解决方案

### 1. 本地知识库管理

#### 文件结构
```
docs/
├── knowledge_base/
│   ├── mcp/
│   │   ├── 01_getting_started.md
│   │   ├── 02_architecture.md
│   │   ├── 03_best_practices.md
│   │   └── 04_troubleshooting.md
│   ├── taskhub/
│   │   ├── architecture_overview.md
│   │   ├── api_reference.md
│   │   └── deployment_guide.md
│   └── index.md
```

#### 知识索引文件
创建 `docs/knowledge_index.json`：
```json
{
  "mcp": {
    "title": "MCP技术栈",
    "description": "Model Context Protocol相关文档",
    "documents": [
      {
        "id": "mcp-001",
        "title": "MCP学习指南",
        "file": "docs/mcp_learning_guide.md",
        "tags": ["mcp", "protocol", "basics"],
        "created_at": "2025-08-10T14:45:00Z"
      },
      {
        "id": "mcp-002", 
        "title": "MCP实战教程",
        "file": "docs/mcp_practical_tutorial.md",
        "tags": ["mcp", "tutorial", "hands-on"],
        "created_at": "2025-08-10T14:46:00Z"
      },
      {
        "id": "mcp-003",
        "title": "MCP最佳实践",
        "file": "docs/mcp_best_practices.md",
        "tags": ["mcp", "best-practices", "design-patterns"],
        "created_at": "2025-08-10T14:47:00Z"
      }
    ]
  }
}
```

### 2. 知识库搜索工具

创建 `src/taskhub/tools/knowledge_search.py`：
```python
import json
import os
from typing import List, Dict, Any
import re

class LocalKnowledgeBase:
    def __init__(self, base_path: str = "docs"):
        self.base_path = base_path
        self.index_file = os.path.join(base_path, "knowledge_index.json")
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        if os.path.exists(self.index_file):
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def search_documents(self, query: str, domain: str = None) -> List[Dict[str, Any]]:
        """搜索文档"""
        results = []
        query_lower = query.lower()
        
        for domain_key, domain_data in self.index.items():
            if domain and domain != domain_key:
                continue
                
            for doc in domain_data.get('documents', []):
                # 搜索标题和标签
                title_match = query_lower in doc['title'].lower()
                tag_match = any(query_lower in tag.lower() for tag in doc.get('tags', []))
                
                if title_match or tag_match:
                    # 读取文件内容进行全文搜索
                    content = self._read_document_content(doc['file'])
                    content_match = query_lower in content.lower()
                    
                    doc_result = {
                        **doc,
                        'content_snippet': self._get_snippet(content, query_lower),
                        'relevance': self._calculate_relevance(title_match, tag_match, content_match)
                    }
                    results.append(doc_result)
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)
    
    def _read_document_content(self, file_path: str) -> str:
        """读取文档内容"""
        full_path = os.path.join(self.base_path, file_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""
    
    def _get_snippet(self, content: str, query: str, max_length: int = 200) -> str:
        """获取内容摘要"""
        if not query or not content:
            return content[:max_length] + "..." if len(content) > max_length else content
        
        # 查找查询词位置
        index = content.lower().find(query.lower())
        if index == -1:
            return content[:max_length] + "..."
        
        start = max(0, index - 50)
        end = min(len(content), index + len(query) + 50)
        snippet = content[start:end]
        
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def _calculate_relevance(self, title_match: bool, tag_match: bool, content_match: bool) -> int:
        """计算相关性分数"""
        score = 0
        if title_match:
            score += 3
        if tag_match:
            score += 2
        if content_match:
            score += 1
        return score
    
    def add_document(self, domain: str, document: Dict[str, Any]) -> bool:
        """添加文档到知识库"""
        if domain not in self.index:
            self.index[domain] = {
                "title": domain,
                "description": f"{domain}相关文档",
                "documents": []
            }
        
        self.index[domain]["documents"].append(document)
        self._save_index()
        return True
    
    def _save_index(self):
        """保存索引文件"""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, indent=2, ensure_ascii=False)

# 创建全局实例
knowledge_base = LocalKnowledgeBase()
```

### 3. 集成到MCP工具

在 `src/taskhub/mcp_server.py` 中添加知识库工具：

```python
from taskhub.tools.knowledge_search import knowledge_base

@mcp.tool()
def search_knowledge(query: str, domain: str = None) -> List[Dict[str, Any]]:
    """搜索知识库文档
    
    Args:
        query: 搜索关键词
        domain: 知识域（可选，如mcp, taskhub等）
    
    Returns:
        匹配的文档列表
    """
    return knowledge_base.search_documents(query, domain)

@mcp.tool()
def add_knowledge_document(
    domain: str,
    title: str,
    file_path: str,
    tags: List[str] = None
) -> Dict[str, Any]:
    """添加文档到知识库
    
    Args:
        domain: 知识域
        title: 文档标题
        file_path: 文件路径（相对于docs目录）
        tags: 标签列表
    
    Returns:
        添加结果
    """
    document = {
        "id": f"{domain}-{int(time.time())}",
        "title": title,
        "file": file_path,
        "tags": tags or [],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    success = knowledge_base.add_document(domain, document)
    return {
        "success": success,
        "document": document if success else None
    }

@mcp.tool()
def list_knowledge_domains() -> List[str]:
    """列出所有知识域"""
    return list(knowledge_base.index.keys())

@mcp.tool()
def get_document_content(file_path: str) -> str:
    """获取文档完整内容
    
    Args:
        file_path: 文件路径（相对于docs目录）
    
    Returns:
        文档内容
    """
    return knowledge_base._read_document_content(file_path)
```

## 服务恢复后的迁移

当Outline服务恢复后，可以执行以下迁移步骤：

### 1. 检查服务状态
```bash
# 检查Outline服务
curl -I http://localhost:3000/api/health
```

### 2. 迁移脚本
创建 `scripts/migrate_knowledge.py`：
```python
import json
import requests
from pathlib import Path

class KnowledgeMigrator:
    def __init__(self, outline_url: str, api_token: str):
        self.outline_url = outline_url
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def migrate_from_local(self, local_index_path: str):
        """从本地知识库迁移到Outline"""
        with open(local_index_path, 'r') as f:
            local_kb = json.load(f)
        
        for domain, data in local_kb.items():
            # 创建知识域
            collection_id = self.create_collection(domain, data.get('description', ''))
            
            # 添加文档
            for doc in data.get('documents', []):
                self.create_document(collection_id, doc)
    
    def create_collection(self, name: str, description: str) -> str:
        """创建知识域"""
        url = f"{self.outline_url}/api/collections.create"
        payload = {
            "name": name,
            "description": description
        }
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()['data']['id']
    
    def create_document(self, collection_id: str, doc: dict):
        """创建文档"""
        url = f"{self.outline_url}/api/documents.create"
        
        # 读取文件内容
        file_path = Path("docs") / doc['file']
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        payload = {
            "collectionId": collection_id,
            "title": doc['title'],
            "content": content,
            "publish": True
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        return response.json()

# 使用示例
if __name__ == "__main__":
    migrator = KnowledgeMigrator(
        outline_url="http://localhost:3000",
        api_token="your-api-token-here"
    )
    migrator.migrate_from_local("docs/knowledge_index.json")
```

## 使用示例

### 1. 搜索知识
```python
# 搜索MCP相关文档
results = knowledge_base.search_documents("MCP协议", "mcp")

# 搜索所有文档
results = knowledge_base.search_documents("最佳实践")
```

### 2. 添加新文档
```python
# 添加新的MCP文档
knowledge_base.add_document("mcp", {
    "id": "mcp-004",
    "title": "MCP性能调优",
    "file": "knowledge_base/mcp/05_performance_tuning.md",
    "tags": ["mcp", "performance", "optimization"],
    "created_at": "2025-08-10T15:00:00Z"
})
```

## 环境配置

### 1. 环境变量设置
创建 `.env` 文件：
```bash
# Outline配置
OUTLINE_URL=http://localhost:3000
OUTLINE_API_TOKEN=your-api-token-here

# 本地知识库配置
LOCAL_KB_ENABLED=true
LOCAL_KB_PATH=docs
```

### 2. 启动本地知识库服务
```bash
# 启动简单的HTTP服务来提供知识库访问
python -m http.server 8080 --directory docs
```

这样即使Outline服务暂时不可用，你也可以通过本地文件系统管理和搜索知识库内容。