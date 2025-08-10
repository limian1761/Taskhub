"""通用工具工具函数和基类，用于减少代码重复。"""

import inspect
from typing import Any, Dict, List, Optional, Callable, get_type_hints, get_origin, get_args
from datetime import datetime, date
from uuid import UUID
from mcp import types
from functools import wraps


def create_tool_definition(func: Callable, name: Optional[str] = None) -> types.Tool:
    """通用的工具定义创建函数，支持增强的类型处理。
    
    Args:
        func: 要创建工具定义的函数
        name: 工具名称，如果为None则使用函数名
    
    Returns:
        MCP Tool 定义
    """
    tool_name = name or f"taskhub.{func.__name__}"
    
    sig = inspect.signature(func)
    properties = {}
    required = []
    
    # 跳过第一个参数（通常是ctx）
    parameters = list(sig.parameters.items())
    if parameters and parameters[0][0] == 'ctx':
        parameters = parameters[1:]
    
    for param_name, param in parameters:
        param_type = param.annotation if param.annotation != inspect.Parameter.empty else str
        
        # 构建JSON Schema
        schema = {"type": "string", "description": f"Parameter {param_name}"}
        
        # 处理基本类型
        if param_type == str:
            schema["type"] = "string"
        elif param_type == int:
            schema["type"] = "integer"
        elif param_type == bool:
            schema["type"] = "boolean"
        elif param_type == float:
            schema["type"] = "number"
        elif param_type == dict:
            schema["type"] = "object"
        elif param_type == list:
            schema["type"] = "array"
        elif param_type == datetime:
            schema.update({"type": "string", "format": "date-time"})
        elif param_type == date:
            schema.update({"type": "string", "format": "date"})
        elif param_type == UUID:
            schema.update({"type": "string", "format": "uuid"})
        else:
            # 处理Optional/Union类型
            origin = get_origin(param_type)
            if origin is not None:
                args = get_args(param_type)
                
                if origin is list or str(origin) == "typing.List":
                    schema["type"] = "array"
                    if args:
                        item_type = args[0]
                        if item_type == str:
                            schema["items"] = {"type": "string"}
                        elif item_type == int:
                            schema["items"] = {"type": "integer"}
                        elif item_type == dict:
                            schema["items"] = {"type": "object"}
                elif origin is dict or str(origin) == "typing.Dict":
                    schema["type"] = "object"
                elif str(origin).startswith("typing.Union") or str(origin).startswith("typing.Optional"):
                    # Optional类型处理
                    non_none_types = [t for t in args if t != type(None)]
                    if non_none_types:
                        actual_type = non_none_types[0]
                        if actual_type == str:
                            schema["type"] = "string"
                        elif actual_type == int:
                            schema["type"] = "integer"
                        elif actual_type == bool:
                            schema["type"] = "boolean"
                        elif actual_type == float:
                            schema["type"] = "number"
                        elif actual_type == datetime:
                            schema.update({"type": "string", "format": "date-time"})
                        elif actual_type == date:
                            schema.update({"type": "string", "format": "date"})
                        elif actual_type == UUID:
                            schema.update({"type": "string", "format": "uuid"})
        
        # 设置默认值
        if param.default != inspect.Parameter.empty:
            schema["default"] = param.default
        else:
            required.append(param_name)
        
        properties[param_name] = schema
    
    return types.Tool(
        name=tool_name,
        description=func.__doc__ or f"Tool {tool_name}",
        inputSchema={
            "type": "object",
            "properties": properties,
            "required": required
        }
    )


class ToolRegistry:
    """通用工具注册器，用于统一管理工具定义和函数映射。"""
    
    def __init__(self, prefix: str = "taskhub"):
        self.prefix = prefix
        self.tools: List[types.Tool] = []
        self.functions: Dict[str, Callable] = {}
    
    def register(self, func: Callable, name: Optional[str] = None) -> None:
        """注册一个工具函数。
        
        Args:
            func: 要注册的函数
            name: 工具名称，如果为None则自动生成
        """
        tool_name = name or f"{self.prefix}.{func.__name__}"
        tool_def = create_tool_definition(func, tool_name)
        
        self.tools.append(tool_def)
        self.functions[tool_name] = func
    
    def register_multiple(self, funcs: List[Callable], prefix: Optional[str] = None) -> None:
        """批量注册多个函数。
        
        Args:
            funcs: 要注册的函数列表
            prefix: 前缀，如果提供则覆盖默认前缀
        """
        current_prefix = prefix or self.prefix
        for func in funcs:
            tool_name = f"{current_prefix}.{func.__name__}"
            self.register(func, tool_name)
    
    def get_tools(self) -> List[types.Tool]:
        """获取所有工具定义。"""
        return self.tools
    
    def get_function(self, name: str) -> Optional[Callable]:
        """根据名称获取函数。"""
        return self.functions.get(name)
    
    def has_function(self, name: str) -> bool:
        """检查是否存在指定名称的函数。"""
        return name in self.functions
    
    def create_mcp_handlers(self, app):
        """为MCP应用创建处理器。
        
        Args:
            app: MCP服务器应用实例
        """
        @app.list_tools()
        async def list_tools():
            return self.tools
        
        @app.call_tool()
        async def call_tool(name: str, arguments: dict[str, Any] | None = None):
            if not self.has_function(name):
                raise ValueError(f"Tool {name} not found")
            
            func = self.get_function(name)
            return await func(None, **(arguments or {}))


def create_mock_context(hunter_id: str = "mock_hunter"):
    """创建模拟的上下文对象，用于测试和工具调用。
    
    Args:
        hunter_id: 猎人ID
    
    Returns:
        模拟的上下文对象
    """
    class MockSession:
        def __init__(self):
            self.hunter_id = hunter_id
    
    class MockRequestContext:
        def __init__(self):
            self.request = None
    
    class MockContext:
        def __init__(self):
            self.request_context = MockRequestContext()
            self.session = MockSession()
    
    return MockContext()


def validate_skills_dict(skills: Any, field_name: str = "skills") -> None:
    """统一的技能字典验证函数。
    
    Args:
        skills: 要验证的技能字典
        field_name: 字段名称用于错误提示
    
    Raises:
        ValidationError: 验证失败时抛出
    """
    from taskhub.utils.error_handler import ValidationError, validate_string_length
    
    if not isinstance(skills, dict):
        raise ValidationError(f"{field_name} must be a dictionary", field=field_name)
    
    for skill_name, skill_level in skills.items():
        if not isinstance(skill_name, str):
            raise ValidationError(f"All skill names in {field_name} must be strings", field=field_name)
        validate_string_length(skill_name, 1, 50, f"skill name in {field_name}")
        
        if not isinstance(skill_level, int):
            raise ValidationError(f"All skill levels in {field_name} must be integers", field=field_name)
        
        if skill_level < 0 or skill_level > 100:
            raise ValidationError(f"Skill levels in {field_name} must be between 0 and 100", field=field_name)


def run_scheduled_task(task_func: Callable, config_func: Callable = None):
    """通用调度任务运行器。
    
    Args:
        task_func: 要运行的任务函数
        config_func: 配置获取函数，如果为None则使用默认配置
    """
    import asyncio
    from taskhub.storage.sqlite_store import SQLiteStore
    
    async def _run_task():
        try:
            if config_func:
                db_path = config_func()
            else:
                from taskhub.config import get_config
                config = get_config()
                db_path = config.get_database_config()["path"]
            
            store = SQLiteStore(db_path)
            await store.connect()
            try:
                await task_func(store)
            finally:
                await store.close()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Scheduled task failed: {e}", exc_info=True)
    
    asyncio.run(_run_task())