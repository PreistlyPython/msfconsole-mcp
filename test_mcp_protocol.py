#!/usr/bin/env python3
"""Test MCP JSON protocol communication"""

import json
import subprocess
import sys

# Test initialize request
init_request = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    },
    "id": 1
}

# Launch the MCP server
proc = subprocess.Popen(
    ["./launch_mcp_for_claude.sh"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

try:
    # Send initialize request
    request_str = json.dumps(init_request) + "\n"
    proc.stdin.write(request_str)
    proc.stdin.flush()
    
    # Read response
    response_line = proc.stdout.readline()
    print(f"Response: {response_line}")
    
    # Check if it's valid JSON
    try:
        response = json.loads(response_line)
        print("Valid JSON response received!")
        print(json.dumps(response, indent=2))
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}")
        print(f"Raw response: {repr(response_line)}")
        
        # Check stderr for errors
        stderr_output = proc.stderr.read()
        if stderr_output:
            print(f"Stderr output: {stderr_output}")
            
except Exception as e:
    print(f"Error during test: {e}")
finally:
    proc.terminate()