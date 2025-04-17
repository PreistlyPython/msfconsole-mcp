#!/usr/bin/env python3

"""
Simple launcher for the MCP server
"""

import os
import sys

# Add parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import and run the server
try:
    from msfconsole_mcp_improved import mcp
    print("Successfully imported MCP, starting server...")
    mcp.run()
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error running server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
