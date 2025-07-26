# Taskhub Usage Guide

## Quick Start

### 1. Start Services

#### Start Taskhub-API Service
```bash
cd taskhub
npm run api
```
Service will start at http://localhost:3000

#### Start Taskhub-Scheduler Service (Optional)
```bash
npm run scheduler
```

### 2. Create Tasks

#### Create Tasks Using Node.js Script
Run the created test script:
```bash
node test_task.js
```

#### Create Tasks Using curl
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "Point Cloud Data Preprocessing",
      "capability": "pointcloud_processing",
      "priority": "High",
      "description": "Denoising and filtering of raw point cloud data"
    },
    "id": 1
  }'
```

#### Supported Parameters
- **name**: Task name (required)
- **capability**: Required capability (required)
- **priority**: Priority (Critical/High/Medium/Low, default Medium)
- **parent_task_id**: Parent task ID (optional)
- **depends_on**: Array of dependent task IDs (optional)
- **description**: Task description (optional)

### 3. List Tasks

#### Get All Tasks
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_list",
    "id": 2
  }'
```

#### Filter Tasks by Criteria
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

### 4. Claim Tasks

#### Agent Claims Task
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

### 5. Update Task Status

#### Update Task Status
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

#### Supported Status Updates
- **pending**: Pending
- **claimed**: Claimed
- **in_progress**: In Progress
- **completed**: Completed
- **failed**: Failed
- **cancelled**: Cancelled

### 6. Register Agents

#### Register New Agent
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

### 7. View Dashboard

Open browser and visit: http://localhost:3000/api/dashboard

## Practical Usage Scenarios

### Scenario 1: Creating Geometric Processing Tasks
```bash
# Create main task
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "Building Model Reconstruction",
      "capability": "3d_reconstruction",
      "priority": "High",
      "description": "Reconstruct 3D building model from point cloud data"
    },
    "id": 1
  }'

# Create sub-task
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "Point Cloud Preprocessing",
      "capability": "pointcloud_processing",
      "priority": "High",
      "parent_task_id": "task-main123",
      "description": "Clean and preprocess raw point cloud data"
    },
    "id": 2
  }'
```

### Scenario 2: Handling Dependencies
```bash
# Create Task A
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "Data Preprocessing",
      "capability": "data_preprocessing",
      "priority": "High"
    },
    "id": 1
  }'

# Create Task B, dependent on Task A
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "task_create",
    "params": {
      "name": "Feature Extraction",
      "capability": "feature_extraction",
      "priority": "Medium",
      "depends_on": ["task-abc123"]
    },
    "id": 2
  }'
```

## Troubleshooting

### Port Conflict Issues
If port 3000 is occupied, you can change the port number:
```bash
PORT=3001 npm run api
```

### Service Startup Failures
1. Check if dependencies are installed:
   ```bash
   npm install
   ```

2. Check if data files exist:
   ```bash
   ls data/taskhub_active.json
   ls data/taskhub_archive.json
   ```

3. Reset data files:
   ```bash
   npm run dev:api
   ```

### Task Creation Failures
Ensure required parameters are provided:
- name: Task name
- capability: Required capability

## Monitoring and Debugging

### View Task Status
Visit Dashboard: http://localhost:3000/api/dashboard

### View Service Logs
API service logs are output directly to the terminal, allowing real-time viewing of task processing.

### Test Connection
```bash
curl http://localhost:3000/health
```

Expected response:
```json
{"status":"ok","service":"Taskhub-API"}
```

### Adding MCP in Cursor
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