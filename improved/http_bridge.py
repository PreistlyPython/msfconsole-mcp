#!/usr/bin/env python3
"""
Simple HTTP server bridge for improved MCP
"""
import sys
import os

try:
    # Import the MCP module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import msfconsole_mcp_improved
    
    # Start HTTP server
    print(f"Starting HTTP server for Improved Metasploit MCP on port 8001...")
    msfconsole_mcp_improved.mcp.run_http_server(host="localhost", port=8001)
except Exception as e:
    print(f"Error starting HTTP server: {e}")
    import traceback
    traceback.print_exc()
