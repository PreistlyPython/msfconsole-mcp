#!/usr/bin/env python3

"""
HTTP server wrapper for the improved Metasploit MCP
This allows the MCP Inspector to connect via HTTP
"""

import sys
import os
import importlib.util

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the MCP module
try:
    # Load the module
    module_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "msfconsole_mcp_improved.py")
    spec = importlib.util.spec_from_file_location("msfconsole_mcp_improved", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the mcp instance
    mcp = module.mcp
    
    # Run the HTTP server
    print(f"Starting HTTP server for Improved Metasploit MCP on port 8000...")
    mcp.run_http_server(host="localhost", port=8000)
except Exception as e:
    print(f"Error starting HTTP server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
