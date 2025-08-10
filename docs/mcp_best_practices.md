# MCP最佳实践与设计模式

## 架构设计原则

### 1. 单一职责原则 (SRP)
每个MCP工具应该专注于一个特定的功能，避免过于复杂的工具设计。

**反例：**
```python
@mcp.tool()
def do_everything(action: str, data: dict) -> dict:
    """一个工具处理所有操作"""
    # 过于复杂的实现...
    pass
```

**正例：**
```python
@mcp.tool()
def create_user(name: str, email: str) -> dict:
    """创建新用户"""
    pass

@mcp.tool()
def update_user_email(user_id: int, new_email: str) -> dict:
    """更新用户邮箱"""
    pass
```

### 2. 分层架构模式
将MCP服务器分为清晰的层次结构：

```
MCP Server
├── API层 (mcp.tools)
├── 服务层 (business logic)
├── 数据层 (database/models)
└── 工具层 (utilities)
```

## 错误处理最佳实践

### 1. 标准化错误响应
```python
from typing import Dict, Any, Union

class MCPErrors:
    INVALID_INPUT = "INVALID_INPUT"
    NOT_FOUND = "NOT_FOUND"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

@mcp.tool()
def safe_api_call(endpoint: str) -> Dict[str, Any]:
    """安全的API调用示例"""
    try:
        if not endpoint.startswith('http'):
            return {
                "success": False,
                "error": {
                    "code": MCPErrors.INVALID_INPUT,
                    "message": "无效的URL格式",
                    "details": "URL必须以http://或https://开头"
                }
            }
        
        # 实际API调用逻辑
        result = call_external_api(endpoint)
        return {"success": True, "data": result}
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": {
                "code": MCPErrors.INTERNAL_ERROR,
                "message": "请求超时",
                "details": "外部服务响应超时，请稍后重试"
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": {
                "code": MCPErrors.INTERNAL_ERROR,
                "message": "内部错误",
                "details": str(e)
            }
        }
```

### 2. 参数验证模式
```python
from pydantic import BaseModel, validator
from typing import Optional

class TaskInput(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int = 1
    
    @validator('title')
    def validate_title(cls, v):
        if len(v) < 2:
            raise ValueError('标题长度必须至少2个字符')
        return v
    
    @validator('priority')
    def validate_priority(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('优先级必须在1-5之间')
        return v

@mcp.tool()
def create_validated_task(
    title: str,
    description: str = None,
    priority: int = 1
) -> dict:
    """使用Pydantic验证的创建任务工具"""
    try:
        task_input = TaskInput(
            title=title,
            description=description,
            priority=priority
        )
        
        # 使用验证后的数据
        return create_task_logic(task_input.dict())
        
    except ValueError as e:
        return {"success": False, "error": str(e)}
```

## 性能优化策略

### 1. 缓存模式
```python
import asyncio
from functools import lru_cache
from typing import Dict, Any
import time

class CacheManager:
    def __init__(self, ttl: int = 300):  # 5分钟TTL
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Any:
        if key in self._cache:
            if time.time() - self._timestamps[key] < self.ttl:
                return self._cache[key]
            else:
                # 过期清理
                del self._cache[key]
                del self._timestamps[key]
        return None
    
    def set(self, key: str, value: Any):
        self._cache[key] = value
        self._timestamps[key] = time.time()

# 全局缓存实例
cache = CacheManager()

@mcp.tool()
def get_cached_data(key: str) -> Dict[str, Any]:
    """带缓存的数据获取"""
    cached_result = cache.get(key)
    if cached_result:
        return {"cached": True, "data": cached_result}
    
    # 获取新数据
    fresh_data = expensive_operation(key)
    cache.set(key, fresh_data)
    
    return {"cached": False, "data": fresh_data}
```

### 2. 连接池管理
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# 优化的数据库连接配置
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600
)

class DatabaseManager:
    def __init__(self):
        self.engine = engine
        self.session_factory = sessionmaker(bind=engine)
    
    def get_session(self):
        return self.session_factory()

# 单例模式
db_manager = DatabaseManager()

@mcp.tool()
def efficient_db_operation():
    """高效的数据库操作"""
    session = db_manager.get_session()
    try:
        # 数据库操作
        pass
    finally:
        session.close()
```

## 安全最佳实践

### 1. 输入清理和验证
```python
import re
from typing import List

def sanitize_input(text: str) -> str:
    """清理用户输入"""
    # 移除潜在的恶意字符
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

@mcp.tool()
def safe_search(query: str) -> List[str]:
    """安全搜索实现"""
    # 清理输入
    clean_query = sanitize_input(query)
    
    # 长度限制
    if len(clean_query) > 100:
        raise ValueError("搜索查询过长")
    
    # 敏感词检查
    forbidden_words = ["admin", "password", "secret"]
    if any(word in clean_query.lower() for word in forbidden_words):
        raise ValueError("查询包含不允许的关键词")
    
    return perform_search(clean_query)
```

### 2. 权限控制
```python
from enum import Enum
from typing import Optional

class PermissionLevel(Enum):
    PUBLIC = 1
    AUTHENTICATED = 2
    ADMIN = 3

class PermissionManager:
    def __init__(self):
        self.permissions = {}
    
    def check_permission(self, user_id: str, required_level: PermissionLevel) -> bool:
        """检查用户权限"""
        user_level = self.get_user_permission_level(user_id)
        return user_level.value >= required_level.value
    
    def get_user_permission_level(self, user_id: str) -> PermissionLevel:
        # 实际实现中从数据库获取
        return PermissionLevel.PUBLIC

permission_manager = PermissionManager()

@mcp.tool()
def admin_only_operation(user_id: str, action: str) -> dict:
    """管理员专属操作"""
    if not permission_manager.check_permission(user_id, PermissionLevel.ADMIN):
        return {"success": False, "error": "权限不足"}
    
    # 执行管理员操作
    return perform_admin_action(action)
```

## 测试策略

### 1. 单元测试模式
```python
import pytest
from unittest.mock import Mock, patch

class TestMCPTools:
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @patch('src.services.TaskService')
    def test_create_task_success(self, mock_service_class):
        """测试成功创建任务"""
        # 设置mock
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.create_task.return_value = Mock(
            id=1,
            title="测试任务",
            description="描述",
            priority=1
        )
        
        # 调用工具
        result = create_task("测试任务", "描述", 1)
        
        # 断言
        assert result["id"] == 1
        assert result["title"] == "测试任务"
    
    @patch('src.services.TaskService')
    def test_create_task_validation_error(self, mock_service_class):
        """测试参数验证错误"""
        mock_service = Mock()
        mock_service_class.return_value = mock_service
        mock_service.create_task.side_effect = ValueError("无效参数")
        
        result = create_task("", "", 10)
        assert "error" in result
```

### 2. 集成测试
```python
import pytest
from fastmcp import Client

class TestMCPServerIntegration:
    
    @pytest.fixture
    def mcp_client(self):
        """创建MCP客户端用于测试"""
        return Client("python run_server.py")
    
    def test_full_workflow(self, mcp_client):
        """测试完整工作流程"""
        # 创建任务
        create_result = mcp_client.call_tool("create_task", {
            "title": "集成测试任务",
            "description": "测试完整流程",
            "priority": 3
        })
        
        task_id = create_result["id"]
        
        # 获取任务
        get_result = mcp_client.call_tool("get_task", {"task_id": task_id})
        assert get_result["title"] == "集成测试任务"
        
        # 更新状态
        update_result = mcp_client.call_tool("update_task_status", {
            "task_id": task_id,
            "status": "completed"
        })
        assert update_result["status"] == "completed"
        
        # 清理
        mcp_client.call_tool("delete_task", {"task_id": task_id})
```

## 部署最佳实践

### 1. Docker化部署
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY src/ ./src/

# 创建非root用户
RUN useradd -m -u 1000 mcpuser
USER mcpuser

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

EXPOSE 8000
CMD ["python", "-m", "src.server"]
```

### 2. 环境配置
```yaml
# docker-compose.yml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mcpdb
      - LOG_LEVEL=INFO
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=mcpdb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 监控和日志

### 1. 结构化日志
```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def log_tool_call(self, tool_name: str, params: dict, result: dict, duration: float):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "tool_call",
            "tool": tool_name,
            "params": params,
            "success": "error" not in result,
            "duration_ms": duration * 1000,
            "result_size": len(str(result))
        }
        self.logger.info(json.dumps(log_entry))

logger = StructuredLogger("mcp.server")

@mcp.tool()
def monitored_tool(**params):
    start_time = time.time()
    result = actual_tool_logic(**params)
    duration = time.time() - start_time
    logger.log_tool_call("tool_name", params, result, duration)
    return result
```

### 2. 性能指标
```python
from prometheus_client import Counter, Histogram, Gauge

# 定义指标
TOOL_CALLS_TOTAL = Counter('mcp_tool_calls_total', 'Total tool calls', ['tool_name'])
TOOL_CALL_DURATION = Histogram('mcp_tool_call_duration_seconds', 'Tool call duration', ['tool_name'])
ACTIVE_CONNECTIONS = Gauge('mcp_active_connections', 'Active MCP connections')

@mcp.tool()
def instrumented_tool():
    TOOL_CALLS_TOTAL.labels(tool_name="my_tool").inc()
    
    with TOOL_CALL_DURATION.labels(tool_name="my_tool").time():
        return actual_tool_logic()
```

## 总结

遵循这些最佳实践可以帮助你构建：
- **可维护**：清晰的代码结构和文档
- **可扩展**：易于添加新功能
- **可靠**：完善的错误处理和监控
- **安全**：输入验证和权限控制
- **高性能**：缓存和连接池优化

记住，最佳实践不是教条，而是根据具体场景灵活应用的经验总结。