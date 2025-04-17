#!/usr/bin/env python3
import sys
import os

# Add directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP module
import msfconsole_mcp_improved

# Run HTTP server
print("Starting HTTP server on http://localhost:8000...")
msfconsole_mcp_improved.mcp.run_http_server(host="localhost", port=8000)
