#!/usr/bin/env python3
"""
Taskhub Client - Python client for interacting with Taskhub MCP server

This script provides a Python interface to interact with the Taskhub system,
allowing you to create tasks, list tasks, claim tasks, update tasks, and 
register agents.
"""

import json
import requests
import uuid
from typing import Dict, Any, Optional, List


class TaskhubClient:
    """
    A client for interacting with the Taskhub MCP server.
    """
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        """
        Initialize the Taskhub client.
        
        Args:
            base_url: The base URL of the Taskhub API server
        """
        self.base_url = base_url
        self.mcp_url = f"{base_url}/mcp"
        self.agent_id = None

    def set_agent_id(self, agent_id: str):
        """
        Set the agent ID for subsequent requests.
        
        Args:
            agent_id: The unique identifier for this agent
        """
        self.agent_id = agent_id

    def _make_request(self, method: str, params: Optional[Dict] = None) -> Dict:
        """
        Make a JSON-RPC request to the Taskhub MCP server.
        
        Args:
            method: The method name to call
            params: Optional parameters for the method
            
        Returns:
            The response from the server
        """
        if params is None:
            params = {}
            
        # Add agent_id to params if it's set and not already provided
        if self.agent_id and 'agent_id' not in params:
            params['agent_id'] = self.agent_id
            
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": str(uuid.uuid4())
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.mcp_url, 
                                data=json.dumps(payload), 
                                headers=headers)
        response.raise_for_status()
        
        return response.json()

    def agent_register(self, agent_id: str, capabilities: List[str]) -> Dict:
        """
        Register a new agent or update an existing one.
        
        Args:
            agent_id: The unique ID of the agent
            capabilities: List of capabilities the agent possesses
            
        Returns:
            The registered agent information
        """
        self.set_agent_id(agent_id)
        params = {
            "agent_id": agent_id,
            "capabilities": capabilities
        }
        return self._make_request("agent_register", params)

    def task_create(self, name: str, capability: str, **kwargs) -> Dict:
        """
        Create a new task in the task hub.
        
        Args:
            name: The name of the task
            capability: The capability required to perform the task
            **kwargs: Additional optional parameters like parent_task_id, depends_on, etc.
            
        Returns:
            The created task information
        """
        params = {
            "name": name,
            "capability": capability,
            **kwargs
        }
        return self._make_request("task_create", params)

    def task_list(self, status: Optional[str] = None, capability: Optional[str] = None) -> List[Dict]:
        """
        List tasks, optionally filtering by properties.
        
        Args:
            status: Filter tasks by status (e.g., pending, claimed, completed)
            capability: Filter tasks by required capability
            
        Returns:
            List of tasks matching the criteria
        """
        params = {}
        if status:
            params["status"] = status
        if capability:
            params["capability"] = capability
            
        response = self._make_request("task_list", params)
        return response.get("result", [])

    def task_get(self, task_id: str) -> Dict:
        """
        Get the details of a specific task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            The task information
        """
        params = {"id": task_id}
        return self._make_request("task_get", params)

    def task_claim(self, capability: str, lease_duration_seconds: Optional[int] = None) -> Dict:
        """
        Claim an available task that matches a given capability.
        
        Args:
            capability: The capability to match for claiming a task
            lease_duration_seconds: The duration in seconds for which the task is leased
            
        Returns:
            The claimed task information
        """
        if not self.agent_id:
            raise ValueError("Agent ID must be set before claiming tasks")
            
        params = {
            "capability": capability,
            "agent_id": self.agent_id
        }
        
        if lease_duration_seconds:
            params["lease_duration_seconds"] = lease_duration_seconds
            
        return self._make_request("task_claim", params)

    def task_update(self, task_id: str, status: str, output: Optional[str] = None) -> Dict:
        """
        Update a task's properties, such as its status.
        
        Args:
            task_id: The ID of the task to update
            status: The new status of the task
            output: Optional output or result of the task execution
            
        Returns:
            The updated task information
        """
        if not self.agent_id:
            raise ValueError("Agent ID must be set before updating tasks")
            
        params = {
            "id": task_id,
            "status": status,
            "agent_id": self.agent_id
        }
        
        if output:
            params["output"] = output
            
        return self._make_request("task_update", params)

    def agent_list(self) -> List[Dict]:
        """
        List all registered agents.
        
        Returns:
            List of all registered agents
        """
        response = self._make_request("agent_list")
        return response.get("result", [])


def example_usage():
    """
    Example usage of the TaskhubClient.
    """
    # Initialize the client
    client = TaskhubClient("http://localhost:3000")
    
    # Register an agent
    print("Registering agent...")
    agent = client.agent_register("python-agent-001", ["data-analysis", "web-scraping"])
    print(f"Agent registered: {agent}")
    
    # Create a task
    print("\nCreating task...")
    task = client.task_create(
        name="Analyze website data", 
        capability="data-analysis",
        description="Analyze collected website data for trends"
    )
    print(f"Task created: {task}")
    
    # List pending tasks
    print("\nListing pending tasks...")
    pending_tasks = client.task_list(status="pending")
    print(f"Found {len(pending_tasks)} pending tasks")
    
    # Claim a task
    print("\nClaiming task...")
    claimed_task = client.task_claim("data-analysis")
    if claimed_task.get("result"):
        print(f"Task claimed: {claimed_task['result']}")
        
        # Update task status to completed
        print("\nUpdating task status...")
        updated_task = client.task_update(
            claimed_task["result"]["id"], 
            "completed", 
            "Analysis complete. Found 3 key trends."
        )
        print(f"Task updated: {updated_task}")
    else:
        print("No tasks available to claim")


if __name__ == "__main__":
    # Run example if script is executed directly
    example_usage()