#!/usr/bin/env python3
"""
集成测试：验证所有工具在新上下文系统下正常工作
"""
import asyncio
import sys
import os

# 添加src到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from taskhub.context import get_app_context, set_namespace, set_hunter_id
from taskhub.tools.task_tools import publish_task, list_tasks, get_task
from taskhub.tools.hunter_tools import register_yourself
from taskhub.tools.knowledge_tools import create_domain, list_domains

async def test_integration():
    """测试所有工具在新上下文系统下的集成"""
    print("=== 集成测试开始 ===")
    
    # 设置测试命名空间和猎人ID
    set_namespace("integration_test")
    set_hunter_id("test_hunter_integration")
    
    print(f"设置命名空间: integration_test")
    print(f"设置猎人ID: test_hunter_integration")
    
    try:
        # 测试1: 注册猎人
        print("\n--- 测试1: 注册猎人 ---")
        hunter_result = await register_yourself({"python": 85, "testing": 90})
        print(f"注册猎人成功: {hunter_result['id']}")
        
        # 测试2: 创建知识域
        print("\n--- 测试2: 创建知识域 ---")
        domain = await create_domain("test_integration_domain", "测试集成域")
        print(f"创建知识域成功: {domain['id']}")
        
        # 测试3: 发布任务
        print("\n--- 测试3: 发布任务 ---")
        task = await publish_task(
            name="集成测试任务",
            details="这是一个用于测试新上下文系统的任务",
            required_skill="python",
            priority=1
        )
        print(f"发布任务成功: {task['id']}")
        
        # 测试4: 列出任务
        print("\n--- 测试4: 列出任务 ---")
        tasks = await list_tasks()
        print(f"找到任务数量: {len(tasks)}")
        
        # 测试5: 获取特定任务
        print("\n--- 测试5: 获取特定任务 ---")
        specific_task = await get_task(task['id'])
        print(f"获取任务成功: {specific_task['name']}")
        
        # 测试6: 列出知识域
        print("\n--- 测试6: 列出知识域 ---")
        domains = await list_domains()
        print(f"找到知识域数量: {len(domains)}")
        
        print("\n=== 所有测试通过 ===")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理
        try:
            context = await get_app_context()
            await context.store.close()
            print("清理完成")
        except:
            pass
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_integration())
    if success:
        print("\n✅ 集成测试成功完成！")
    else:
        print("\n❌ 集成测试失败！")
        sys.exit(1)