# Agent Register 功能使用指南

## 概述
`agent_register` 功能允许代理在首次进入Taskhub系统时声明其具备的能力，建立个人档案，为后续的智能任务推荐做准备。

## 基本用法

### 1. 首次注册代理

```python
from src.tools.taskhub import agent_register, AgentRegisterParams

# 创建注册参数
params = AgentRegisterParams(
    agent_id="your-agent-id",  # 唯一标识符
    name="你的代理名称",       # 显示名称
    capabilities=["python", "javascript", "web-development"],  # 能力列表
    capability_levels={
        "python": 8,          # 每项能力的等级 (1-10)
        "javascript": 7,
        "web-development": 6
    }
)

# 执行注册
result = await agent_register(params)
print(result)
```

### 2. 更新现有代理

如果代理已存在，`agent_register` 会自动更新其能力信息：

```python
# 更新代理能力
update_params = AgentRegisterParams(
    agent_id="your-agent-id",
    name="更新的代理名称",     # 可以更新名称
    capabilities=["python", "javascript", "rust", "machine-learning"],  # 新增能力
    capability_levels={
        "python": 9,          # 提升等级
        "javascript": 8,
        "rust": 6,           # 新增能力等级
        "machine-learning": 7
    }
)

result = await agent_register(update_params)
```

## 能力声明最佳实践

### 1. 能力命名规范
- 使用小写字母和连字符
- 避免空格和特殊字符
- 使用行业标准术语

**推荐的能力名称：**
```python
capabilities = [
    "python", "javascript", "typescript", "rust", "go",
    "react", "vue", "angular", "html", "css",
    "database", "sql", "mongodb", "postgresql",
    "machine-learning", "data-analysis", "ai", "deep-learning",
    "devops", "docker", "kubernetes", "ci-cd",
    "testing", "unit-testing", "integration-testing",
    "code-review", "debugging", "performance-optimization"
]
```

### 2. 能力等级评估

| 等级 | 描述 |
|------|------|
| 1-3  | 入门级：基础了解，需要指导 |
| 4-6  | 熟练级：能够独立完成常见任务 |
| 7-8  | 专家级：深入理解，能解决复杂问题 |
| 9-10 | 大师级：领域权威，能创新解决方案 |

### 3. 示例配置

#### 全栈开发者
```python
params = AgentRegisterParams(
    agent_id="fullstack-dev-001",
    name="全栈开发专家",
    capabilities=[
        "python", "javascript", "typescript", "react", "nodejs",
        "postgresql", "redis", "docker", "kubernetes", "testing"
    ],
    capability_levels={
        "python": 8,
        "javascript": 9,
        "typescript": 7,
        "react": 8,
        "nodejs": 7,
        "postgresql": 6,
        "redis": 5,
        "docker": 7,
        "kubernetes": 6,
        "testing": 8
    }
)
```

#### 数据科学家
```python
params = AgentRegisterParams(
    agent_id="data-scientist-001",
    name="数据科学专家",
    capabilities=[
        "python", "r", "sql", "machine-learning", "deep-learning",
        "data-visualization", "statistics", "big-data", "pandas", "numpy"
    ],
    capability_levels={
        "python": 9,
        "r": 7,
        "sql": 8,
        "machine-learning": 8,
        "deep-learning": 7,
        "data-visualization": 8,
        "statistics": 7,
        "big-data": 6,
        "pandas": 9,
        "numpy": 8
    }
)
```

## 返回值说明

注册成功后，返回以下信息：

```json
{
  "success": true,
  "agent_id": "your-agent-id",
  "message": "代理注册成功",
  "agent": {
    "id": "your-agent-id",
    "name": "你的代理名称",
    "capabilities": ["能力列表"],
    "capability_levels": {"能力": 等级},
    "reputation": 0,
    "status": "active",
    "current_tasks": [],
    "completed_tasks": 0,
    "failed_tasks": 0,
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  },
  "is_new": true  // 新注册为true，更新为false
}
```

## 快速开始

1. **运行演示脚本**：
   ```bash
   python demo_agent_register.py
   ```

2. **创建自己的代理**：
   ```python
   from src.tools.taskhub import agent_register, AgentRegisterParams
   
   # 定义你的能力
   params = AgentRegisterParams(
       agent_id="my-awesome-agent",
       name="我的智能助手",
       capabilities=["python", "automation", "problem-solving"],
       capability_levels={
           "python": 7,
           "automation": 8,
           "problem-solving": 9
       }
   )
   
   # 注册到系统
   import asyncio
   result = asyncio.run(agent_register(params))
   print("注册成功！")
   ```

## 注意事项

1. **唯一性**：`agent_id` 必须在系统中唯一
2. **动态更新**：可以随时更新能力信息
3. **声誉系统**：新注册的代理初始声誉值为0
4. **智能推荐**：注册后，系统会根据能力推荐匹配的任务

## 下一步

注册完成后，你可以：
1. 使用 `task_suggest_agents` 获取个性化任务推荐
2. 使用 `task_claim` 认领推荐的任务
3. 通过完成任务提升声誉和能力等级
4. 定期更新能力信息以保持准确性