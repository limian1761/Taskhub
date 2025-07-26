# Taskhub 使用指南

## 快速开始

### 1. 启动服务

#### 启动 Taskhub-API 服务
```bash
cd taskhub
npm run api
```
服务将在 http://localhost:3000 启动

#### 启动 Taskhub-Scheduler 服务（可选）
```bash
npm run scheduler
```

### 2. 创建任务

#### 使用 Node.js 脚本创建任务
运行已创建的测试脚本：
```bash
node test_task.js
```

#### 使用 curl 创建任务
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "点云数据预处理",
      "capability": "pointcloud_processing",
      "priority": "High",
      "description": "对原始点云数据进行降噪和滤波处理"
    },
    "id": 1
  }'
```

#### 支持的参数
- **name**: 任务名称（必需）
- **capability**: 所需能力（必需）
- **priority**: 优先级（Critical/High/Medium/Low，默认Medium）
- **parent_task_id**: 父任务ID（可选）
- **depends_on**: 依赖任务ID数组（可选）
- **description**: 任务描述（可选）

### 3. 列出任务

#### 获取所有任务
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_list",
    "id": 2
  }'
```

#### 按条件筛选任务
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_list",
    "params": {
      "status": "pending",
      "capability": "pointcloud_processing"
    },
    "id": 3
  }'
```

### 4. 认领任务

#### 智能体认领任务
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_claim",
    "params": {
      "capability": "pointcloud_processing",
      "agent_id": "agent-001",
      "lease_duration_seconds": 600
    },
    "id": 4
  }'
```

### 5. 更新任务状态

#### 更新任务状态
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_update",
    "params": {
      "id": "task-abc123",
      "status": "completed",
      "lease_id": "lease-xyz789"
    },
    "id": 5
  }'
```

#### 支持的状态更新
- **pending**: 待处理
- **claimed**: 已认领
- **in_progress**: 进行中
- **completed**: 已完成
- **failed**: 失败
- **cancelled**: 已取消

### 6. 注册智能体

#### 注册新智能体
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "agent_register",
    "params": {
      "agent_id": "agent-001",
      "capabilities": ["pointcloud_processing", "3d_modeling", "data_analysis"]
    },
    "id": 6
  }'
```

### 7. 查看Dashboard

打开浏览器访问：http://localhost:3000/api/dashboard

## 实际使用场景示例

### 场景1：创建几何处理任务
```bash
# 创建主任务
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "建筑模型重建",
      "capability": "3d_reconstruction",
      "priority": "High",
      "description": "从点云数据重建3D建筑模型"
    },
    "id": 1
  }'

# 创建子任务
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "点云预处理",
      "capability": "pointcloud_processing",
      "priority": "High",
      "parent_task_id": "task-main123",
      "description": "清理和预处理原始点云数据"
    },
    "id": 2
  }'
```

### 场景2：处理依赖关系
```bash
# 创建任务A
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "数据预处理",
      "capability": "data_preprocessing",
      "priority": "High"
    },
    "id": 1
  }'

# 创建任务B，依赖任务A
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "特征提取",
      "capability": "feature_extraction",
      "priority": "Medium",
      "depends_on": ["task-abc123"]
    },
    "id": 2
  }'
```

## 常见问题解决

### 端口占用问题
如果端口3000被占用，可以修改端口号：
```bash
PORT=3001 npm run api
```

### 服务启动失败
1. 检查是否已安装依赖：
   ```bash
   npm install
   ```

2. 检查数据文件是否存在：
   ```bash
   ls data/taskhub_active.json
   ls data/taskhub_archive.json
   ```

3. 重置数据文件：
   ```bash
   npm run dev:api
   ```

### 任务创建失败
确保提供必需的参数：
- name: 任务名称
- capability: 所需能力

## 监控和调试

### 查看任务状态
访问Dashboard：http://localhost:3000/api/dashboard

### 查看服务日志
API服务日志会直接输出到终端，可以实时查看任务处理情况。

### 测试连接
```bash
curl http://localhost:3000/health
```

预期返回：
```json
{"status":"ok","service":"Taskhub-API"}
```
### 在Cursor 添加MCP 
```json
{
  "mcpServers": {
    "taskhub": {
      "url": "http://localhost:3000/mcp",
      "headers": {
        "agentId": "KIMI"
      }
    }
  }
}
```
