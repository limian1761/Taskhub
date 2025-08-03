#!/bin/bash

# Set Python path to include project root directory
export PYTHONPATH="$(pwd):$PYTHONPATH"

echo "Starting Taskhub services..."
echo ""

# Start main Taskhub MCP service
echo "Starting Main Taskhub Server on port 3000..."
python -m taskhub --host 0.0.0.0 --port 3000 --reload --reload-dir src &
TASKHUB_PID=$!

# Start Admin service
echo "Starting API Server on port 8000..."
uvicorn src.api_server:app --host 0.0.0.0 --port 8000 --reload --reload-dir src &
API_PID=$!

echo ""
echo "All services started in the background:"
echo "  - Main Taskhub Server PID: $TASKHUB_PID"
echo "  - API Server PID: $API_PID"
echo ""
echo "Use 'kill $TASKHUB_PID $API_PID' or 'pkill -f uvicorn' to stop all services."

# Wait for all background processes so the script can be interrupted with Ctrl+C
wait $TASKHUB_PID $API_PID