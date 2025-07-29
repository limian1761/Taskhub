import subprocess
import json
import sys

def test_stdio_server():
    # Start the Taskhub server in stdio mode
    process = subprocess.Popen(
        [sys.executable, "scripts/launch.py", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1
    )
    
    # Send an initialize message
    initialize_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    # Send the message
    process.stdin.write(json.dumps(initialize_msg) + "\n")
    process.stdin.flush()
    
    # Read the response
    response = process.stdout.readline()
    print("Response:", response)
    
    # Send an exit message
    exit_msg = {
        "jsonrpc": "2.0",
        "method": "exit"
    }
    
    process.stdin.write(json.dumps(exit_msg) + "\n")
    process.stdin.flush()
    
    # Wait for the process to finish
    stdout, stderr = process.communicate()
    print("STDOUT:", stdout)
    print("STDERR:", stderr)
    print("Return code:", process.returncode)

if __name__ == "__main__":
    test_stdio_server()