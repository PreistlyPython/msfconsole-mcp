#!/usr/bin/env python3
"""
Test MCP connection for MSF Console
"""

import json
import subprocess
import sys
import os

# Test MCP handshake
handshake = {
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {
            "name": "test-client",
            "version": "1.0.0"
        }
    },
    "id": 1
}

# Start the server process
cmd = [
    "/home/dell/coding/mcp/msfconsole/venv/bin/python",
    "/home/dell/coding/mcp/msfconsole/mcp_server_stable.py"
]

env = os.environ.copy()
env["PYTHONPATH"] = "/home/dell/coding/mcp/msfconsole"
env["METASPLOIT_FRAMEWORK_ROOT"] = "/usr/share/metasploit-framework"

try:
    print("Starting MSF Console MCP server...")
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Send handshake
    print("Sending handshake...")
    proc.stdin.write(json.dumps(handshake) + "\n")
    proc.stdin.flush()
    
    # Read response
    response_line = proc.stdout.readline()
    if response_line:
        response = json.loads(response_line)
        print("Received response:", json.dumps(response, indent=2))
        
        if "result" in response:
            print("\n✅ MCP connection successful!")
            print(f"Server info: {response['result'].get('serverInfo', {})}")
        else:
            print("\n❌ MCP handshake failed:", response)
    else:
        # Check stderr
        stderr = proc.stderr.read()
        print("\n❌ No response received. Stderr:", stderr)
    
    # Terminate
    proc.terminate()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()