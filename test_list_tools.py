#!/usr/bin/env python3
"""Test listing MCP tools"""

import json
import subprocess
import sys
import time

# Launch the MCP server
proc = subprocess.Popen(
    ["./launch_mcp_for_claude.sh"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=0
)

try:
    # Send initialize request first
    init_request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2025-06-18",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        },
        "id": 1
    }
    
    proc.stdin.write(json.dumps(init_request) + "\n")
    proc.stdin.flush()
    response = proc.stdout.readline()
    print(f"Initialize response: {json.loads(response)['result']['serverInfo']}")
    
    # List tools
    list_tools_request = {
        "jsonrpc": "2.0",
        "method": "tools/list",
        "id": 2
    }
    
    proc.stdin.write(json.dumps(list_tools_request) + "\n")
    proc.stdin.flush()
    
    # Read response
    response_line = proc.stdout.readline()
    response = json.loads(response_line)
    
    print(f"\nFound {len(response['result']['tools'])} tools:")
    for tool in response['result']['tools']:
        print(f"  - {tool['name']}: {tool['description'][:60]}...")
        
except Exception as e:
    print(f"Error: {e}")
    stderr = proc.stderr.read()
    if stderr:
        print(f"Stderr: {stderr}")
finally:
    proc.terminate()