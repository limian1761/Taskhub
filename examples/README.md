# Taskhub Python Client Examples

This directory contains examples showing how to use the Taskhub Python client to interact with the Taskhub system.

## Installation

First, make sure you have the required dependencies installed:

```bash
pip install requests
```

## Files

- [../taskhub_client.py](file:///C:/Users/lichao/OneDrive/dev/Taskhub/taskhub_client.py) - The main Python client library
- [python_client_demo.py](file:///C:/Users/lichao/OneDrive/dev/Taskhub/examples/python_client_demo.py) - A demo script showing how to use the client

## Usage

1. Make sure the Taskhub server is running:
   ```bash
   npm run api
   ```

2. Run the demo script:
   ```bash
   python python_client_demo.py
   ```

## API Reference

The Python client provides methods that correspond to the JSON-RPC methods available in the Taskhub MCP server:

### Initialization

```python
from taskhub_client import TaskhubClient

client = TaskhubClient("http://localhost:3000")
```

### Agent Methods

- `agent_register(agent_id, capabilities)` - Register or update an agent
- `agent_list()` - List all registered agents

### Task Methods

- `task_create(name, capability, **kwargs)` - Create a new task
- `task_list(status=None, capability=None)` - List tasks with optional filtering
- `task_get(task_id)` - Get details of a specific task
- `task_claim(capability, lease_duration_seconds=None)` - Claim a task
- `task_update(task_id, status, output=None)` - Update task status

### Example Workflow

```python
# Initialize client
client = TaskhubClient("http://localhost:3000")

# Register agent
client.agent_register("my-agent", ["data-analysis", "web-scraping"])

# Create a task
task = client.task_create(
    name="Analyze website data",
    capability="data-analysis",
    description="Analyze collected data for trends",
    reward=100
)

# Claim and complete a task
claimed = client.task_claim("data-analysis")
if claimed.get('result'):
    client.task_update(claimed['result']['id'], "completed", "Analysis complete")
```