import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from taskhub.tools.knowledge_tools import register_knowledge_tools

# 创建一个模拟的FastMCP应用
class MockApp:
    def __init__(self):
        self.tools = {}
        self.resources = {}
    
    def tool(self, name=None):
        def decorator(func):
            tool_name = name or func.__name__
            self.tools[tool_name] = func
            return func
        return decorator
    
    def resource(self, pattern):
        def decorator(func):
            self.resources[pattern] = func
            return func
        return decorator

@pytest_asyncio.fixture
def app():
    """创建一个模拟的应用实例"""
    return MockApp()

@pytest_asyncio.fixture
async def mock_context():
    """创建一个模拟的MCP上下文"""
    context = MagicMock()
    context.session.hunter_id = "test-hunter"
    context.request_context = MagicMock()
    return context

@pytest.mark.asyncio
async def test_register_knowledge_tools(app):
    """测试注册知识工具"""
    # 注册工具
    register_knowledge_tools(app)
    
    # 验证工具是否正确注册
    assert "taskhub.knowledge.add" in app.tools
    assert "taskhub.knowledge.list" in app.tools
    assert "taskhub.domain.create" in app.tools

@pytest.mark.asyncio
async def test_add_knowledge_tool(mock_context, app, monkeypatch):
    """测试添加知识工具函数"""
    # 注册工具
    register_knowledge_tools(app)
    
    # 模拟knowledge_add函数
    mock_knowledge = MagicMock()
    mock_knowledge.id = "test-knowledge"
    mock_knowledge.model_dump.return_value = {"id": "test-knowledge", "title": "Test Knowledge"}
    
    # 使用monkeypatch替换实际的knowledge_add函数
    monkeypatch.setattr("taskhub.tools.knowledge_tools.knowledge_add", AsyncMock(return_value=mock_knowledge))
    
    # 调用工具函数
    add_tool = app.tools["taskhub.knowledge.add"]
    result = await add_tool(
        mock_context,
        title="Test Knowledge",
        content="Test Content",
        source="test",
        domain_tags=["domain1"],
    )
    
    # 验证结果
    assert result["id"] == "test-knowledge"
    assert result["title"] == "Test Knowledge"

@pytest.mark.asyncio
async def test_list_knowledge_tool(mock_context, app, monkeypatch):
    """测试列出知识工具函数"""
    # 注册工具
    register_knowledge_tools(app)
    
    # 模拟knowledge_list函数
    mock_knowledge = MagicMock()
    mock_knowledge.id = "test-knowledge"
    mock_knowledge.model_dump.return_value = {"id": "test-knowledge", "title": "Test Knowledge"}
    
    # 使用monkeypatch替换实际的knowledge_list函数
    monkeypatch.setattr("taskhub.tools.knowledge_tools.knowledge_list", AsyncMock(return_value=[mock_knowledge]))
    
    # 调用工具函数
    list_tool = app.tools["taskhub.knowledge.list"]
    result = await list_tool(mock_context)
    
    # 验证结果
    assert len(result) == 1
    assert result[0]["id"] == "test-knowledge"

@pytest.mark.asyncio
async def test_create_domain_tool(mock_context, app, monkeypatch):
    """测试创建领域工具函数"""
    # 注册工具
    register_knowledge_tools(app)
    
    # 模拟domain_create函数
    mock_domain = MagicMock()
    mock_domain.id = "test-domain"
    mock_domain.model_dump.return_value = {"id": "test-domain", "name": "Test Domain"}
    
    # 使用monkeypatch替换实际的domain_create函数
    monkeypatch.setattr("taskhub.tools.knowledge_tools.domain_create", AsyncMock(return_value=mock_domain))
    
    # 调用工具函数
    create_tool = app.tools["taskhub.domain.create"]
    result = await create_tool(mock_context, name="Test Domain", description="Test Description")
    
    # 验证结果
    assert result["id"] == "test-domain"
    assert result["name"] == "Test Domain"