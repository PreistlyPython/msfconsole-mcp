#!/usr/bin/env python3
"""
Simple HTTP server bridge for MCP
"""
import sys
import os

try:
    # Import the MCP module
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import msfconsole_mcp
    
    # Start HTTP server
    print(f"Starting HTTP server for Metasploit MCP on port 8000...")
    msfconsole_mcp.mcp.run_http_server(host="localhost", port=8000)
except Exception as e:
    print(f"Error starting HTTP server: {e}")
    import traceback
    traceback.print_exc()
