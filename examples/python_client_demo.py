#!/usr/bin/env python3
"""
Demo script showing how to use the Taskhub Python client
"""

import sys
import os

# Add the parent directory to the path so we can import taskhub_client
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from taskhub_client import TaskhubClient


def main():
    # Initialize the client
    client = TaskhubClient("http://localhost:3000")
    
    # Register an agent
    print("Registering agent...")
    agent = client.agent_register("demo-python-agent", ["python-programming", "data-analysis"])
    print(f"Registered agent: {agent['result']}")
    
    # Create a sample task
    print("\nCreating a sample task...")
    task = client.task_create(
        name="Process user data", 
        capability="data-analysis",
        description="Process and analyze user data for insights",
        reward=50
    )
    print(f"Created task: {task['result']}")
    
    # List all pending tasks
    print("\nListing all pending tasks...")
    pending_tasks = client.task_list(status="pending")
    print(f"Found {len(pending_tasks['result'])} pending tasks:")
    for task in pending_tasks['result']:
        print(f"  - {task['name']} (ID: {task['id']})")
    
    # Try to claim a task
    print("\nTrying to claim a task...")
    claimed = client.task_claim("data-analysis")
    if claimed.get('result'):
        task_id = claimed['result']['id']
        print(f"Claimed task: {claimed['result']['name']}")
        
        # Update the task as completed
        print("\nMarking task as completed...")
        updated = client.task_update(
            task_id, 
            "completed", 
            "Successfully processed user data and generated insights."
        )
        print(f"Task completed! New reputation: {updated['result'].get('assignee_reputation', 'N/A')}")
    else:
        print("No tasks available to claim")


if __name__ == "__main__":
    main()