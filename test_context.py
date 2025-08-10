#!/usr/bin/env python3
"""
测试新的上下文系统
"""
import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from taskhub.context import get_app_context, set_namespace, set_hunter_id

async def test_context_system():
    """测试新的上下文系统"""
    print("=== 测试新的上下文系统 ===")
    
    # 设置全局命名空间和猎人ID
    set_namespace("test_namespace")
    set_hunter_id("test_hunter_123")
    
    print("设置全局命名空间: test_namespace")
    print("设置全局猎人ID: test_hunter_123")
    
    # 获取应用上下文
    context = await get_app_context()
    
    print(f"获取到的上下文信息:")
    print(f"  命名空间: {context.namespace}")
    print(f"  猎人ID: {context.hunter_id}")
    print(f"  存储实例类型: {type(context.store).__name__}")
    
    # 测试不同的命名空间
    set_namespace("another_namespace")
    set_hunter_id("another_hunter_456")
    
    context2 = await get_app_context()
    print(f"\n更改后的上下文信息:")
    print(f"  命名空间: {context2.namespace}")
    print(f"  猎人ID: {context2.hunter_id}")
    print(f"  存储实例类型: {type(context2.store).__name__}")
    
    # 验证命名空间是否正确应用
    print(f"\n验证命名空间:")
    print(f"  context.namespace: {context.namespace}")
    print(f"  context2.namespace: {context2.namespace}")
    print(f"  预期应该是: another_namespace")
    
    # 清理
    await context.store.close()
    await context2.store.close()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_context_system())