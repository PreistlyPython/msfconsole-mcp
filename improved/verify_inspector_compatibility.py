#!/usr/bin/env python3
"""
This script checks whether our MCP implementation is compatible with the MCP Inspector.
"""
import os
import sys
import inspect
import json

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Import our MCP module
    import msfconsole_mcp_improved
    
    # Get the MCP instance
    mcp_server = msfconsole_mcp_improved.mcp
    
    # Print MCP information
    print(f"MCP Type: {type(mcp_server)}")
    print(f"Available tools: {mcp_server.list_tools()}")
    
    # Check if the necessary methods for the Inspector are present
    required_methods = [
        "list_tools", 
        "call_tool", 
        "run", 
        "run_http_server"
    ]
    
    for method in required_methods:
        if hasattr(mcp_server, method):
            print(f"✓ Has required method: {method}")
        else:
            print(f"✗ Missing required method: {method}")
    
    # Check for any specific issues
    try:
        tools = mcp_server.list_tools()
        for tool in tools:
            print(f"Tool: {tool}")
            tool_info = mcp_server.get_tool_info(tool)
            print(f"  Parameters: {json.dumps(tool_info.get('parameters', {}), indent=2)}")
    except Exception as e:
        print(f"Error inspecting tools: {e}")
    
    print("\nCompatibility check complete.")
except Exception as e:
    print(f"Error during compatibility check: {e}")
    import traceback
    traceback.print_exc()
