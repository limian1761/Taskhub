#!/bin/bash

# This script starts all Taskhub services.
# It launches separate processes for the API service and the MCP service.

# Suppress websockets deprecation warnings globally
export PYTHONWARNINGS="ignore::DeprecationWarning"
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Start API service
echo "Starting Taskhub API Server on http://localhost:8001..."
python -m taskhub api --host localhost --port 8001 &
API_PID=$!

echo "Starting Taskhub MCP Server on http://localhost:8000..."
python -m taskhub mcp --host localhost --port 8000 &
MCP_PID=$!

echo "Taskhub services started."
echo "API service: http://localhost:8001"
echo "MCP service: http://localhost:8000"

echo "Press Ctrl+C to stop all services."
trap "kill $API_PID $MCP_PID" INT TERM
wait $API_PID $MCP_PID