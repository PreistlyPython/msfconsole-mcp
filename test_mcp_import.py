#!/usr/bin/env python3
"""
Test script to verify MCP SDK imports work correctly.
This is a simple diagnostic script to check if the MCP package is properly installed.
"""

import sys
import os

# Print system path for debugging
print("Python version:", sys.version)
print("\nSYSPATH:")
for path in sys.path:
    print(f"  {path}")

# Try importing the MCP module
print("\nAttempting to import MCP modules...")
try:
    from mcp.server.fastmcp import FastMCP, Context
    print("SUCCESS: MCP SDK imported correctly!")
    
    # Try creating a FastMCP instance with error handling
    try:
        # Print MCP module path
        import mcp
        print(f"MCP module path: {mcp.__file__}")
        
        # Try creating a FastMCP instance to make sure it works
        mcp_instance = FastMCP("test", version="0.1.0")
        print("SUCCESS: Created FastMCP instance!")
        
        # Test Context attributes 
        print("\nContext methods and attributes:")
        print(dir(Context))
        
    except Exception as e:
        print(f"WARNING: Error creating FastMCP instance: {e}")
        print("MCP module found but may not be fully functional")
        
except ImportError as e:
    print(f"ERROR: Failed to import MCP SDK: {e}")
    # Try to determine what's available
    try:
        import mcp
        print(f"Found mcp module at: {mcp.__file__}")
        print(f"Available mcp submodules: {dir(mcp)}")
    except ImportError:
        print("mcp module not found in the Python path")
    
    sys.exit(1)
except Exception as e:
    print(f"ERROR: Unexpected error importing MCP SDK: {e}")
    sys.exit(1)

print("\nMCP import tests passed successfully!")
