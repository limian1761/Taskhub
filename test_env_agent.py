#!/usr/bin/env python3
"""
测试脚本：强制使用环境变量作为AgentID和AgentName
"""
import os
import asyncio
from src.tools.taskhub import agent_register, AgentRegisterParams

async def test_env_agent():
    """测试强制使用环境变量作为AgentID和AgentName"""
    
    # 设置环境变量
    os.environ['AGENT_ID'] = 'env-test-agent-001'
    os.environ['AGENT_NAME'] = '环境变量名称代理'
    
    # 测试1：正常使用环境变量
    print("测试1：正常使用环境变量")
    params1 = AgentRegisterParams(
        capabilities=["python", "javascript"],
        capability_levels={"python": 8, "javascript": 6}
    )
    
    result1 = await agent_register(params1)
    print(f"结果：{result1}")
    
    # 测试2：未设置AGENT_ID环境变量
    print("\n测试2：未设置AGENT_ID环境变量")
    if 'AGENT_ID' in os.environ:
        del os.environ['AGENT_ID']
    
    params2 = AgentRegisterParams(
        capabilities=["typescript"],
        capability_levels={"typescript": 7}
    )
    
    result2 = await agent_register(params2)
    print(f"结果：{result2}")
    
    # 测试3：未设置AGENT_NAME环境变量
    print("\n测试3：未设置AGENT_NAME环境变量")
    os.environ['AGENT_ID'] = 'test-agent-003'
    if 'AGENT_NAME' in os.environ:
        del os.environ['AGENT_NAME']
    
    params3 = AgentRegisterParams(
        capabilities=["go"],
        capability_levels={"go": 5}
    )
    
    result3 = await agent_register(params3)
    print(f"结果：{result3}")
    
    # 测试4：恢复环境变量，再次测试成功场景
    print("\n测试4：恢复环境变量，再次测试成功场景")
    os.environ['AGENT_ID'] = 'final-test-agent'
    os.environ['AGENT_NAME'] = '最终测试代理'
    
    params4 = AgentRegisterParams(
        capabilities=["rust", "python"],
        capability_levels={"rust": 4, "python": 9}
    )
    
    result4 = await agent_register(params4)
    print(f"结果：{result4}")

if __name__ == "__main__":
    asyncio.run(test_env_agent())