import pytest
import pytest_asyncio
from unittest.mock import MagicMock, AsyncMock

from taskhub.tools.hunter_tools import register_hunter_tools
from taskhub.models.hunter import Hunter

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
async def test_register_hunter_tools(app):
    """测试注册猎人工具"""
    # 注册工具
    register_hunter_tools(app)
    
    # 验证工具是否正确注册
    assert "taskhub.hunter.register" in app.tools
    assert "taskhub.hunter.list" in app.tools
    assert "taskhub.hunter.get" in app.tools
    assert "taskhub.hunter.study" in app.tools

@pytest.mark.asyncio
async def test_register_hunter_tool(mock_context, app, monkeypatch):
    """测试注册猎人工具函数"""
    # 注册工具
    register_hunter_tools(app)
    
    # 模拟hunter_register函数
    mock_hunter = MagicMock()
    mock_hunter.id = "test-hunter"
    mock_hunter.model_dump.return_value = {"id": "test-hunter", "name": "Test Hunter"}
    
    # 使用monkeypatch替换实际的hunter_register函数
    monkeypatch.setattr("taskhub.tools.hunter_tools.hunter_register", AsyncMock(return_value=mock_hunter))
    
    # 调用工具函数
    register_tool = app.tools["taskhub.hunter.register"]
    result = await register_tool(mock_context, hunter_id="test-hunter", name="Test Hunter")
    
    # 验证结果
    assert result["id"] == "test-hunter"
    assert result["name"] == "Test Hunter"

@pytest.mark.asyncio
async def test_list_hunters_tool(mock_context, app, monkeypatch):
    """测试列出猎人工具函数"""
    # 注册工具
    register_hunter_tools(app)
    
    # 模拟hunter_list函数
    mock_hunter = MagicMock()
    mock_hunter.id = "test-hunter"
    mock_hunter.model_dump.return_value = {"id": "test-hunter", "name": "Test Hunter"}
    
    # 使用monkeypatch替换实际的hunter_list函数
    monkeypatch.setattr("taskhub.tools.hunter_tools.hunter_list", AsyncMock(return_value=[mock_hunter]))
    
    # 调用工具函数
    list_tool = app.tools["taskhub.hunter.list"]
    result = await list_tool(mock_context)
    
    # 验证结果
    assert len(result) == 1
    assert result[0]["id"] == "test-hunter"

@pytest.mark.asyncio
async def test_get_hunter_tool(mock_context, app, monkeypatch):
    """测试获取猎人工具函数"""
    # 注册工具
    register_hunter_tools(app)
    
    # 模拟get_hunter函数
    mock_hunter = MagicMock()
    mock_hunter.id = "test-hunter"
    mock_hunter.model_dump.return_value = {"id": "test-hunter", "name": "Test Hunter"}
    
    # 使用monkeypatch替换实际的get_hunter函数
    monkeypatch.setattr("taskhub.tools.hunter_tools.get_hunter", AsyncMock(return_value=mock_hunter))
    
    # 调用工具函数
    get_tool = app.tools["taskhub.hunter.get"]
    result = await get_tool(mock_context, hunter_id="test-hunter")
    
    # 验证结果
    assert result["id"] == "test-hunter"
    assert result["name"] == "Test Hunter"

@pytest.mark.asyncio
async def test_study_knowledge_tool(mock_context, app, monkeypatch):
    """测试学习知识工具函数"""
    # 注册工具
    register_hunter_tools(app)
    
    # 模拟hunter_study函数
    mock_hunter = MagicMock()
    mock_hunter.id = "test-hunter"
    mock_hunter.model_dump.return_value = {"id": "test-hunter", "domain_scores": {"domain1": 80}}
    
    # 使用monkeypatch替换实际的hunter_study函数
    monkeypatch.setattr("taskhub.tools.hunter_tools.hunter_study", AsyncMock(return_value=mock_hunter))
    
    # 调用工具函数
    study_tool = app.tools["taskhub.hunter.study"]
    result = await study_tool(mock_context, knowledge_id="test-knowledge")
    
    # 验证结果
    assert result["id"] == "test-hunter"
    assert "domain1" in result["domain_scores"]