#!/usr/bin/env python3
import sys
import os
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"Working directory: {os.getcwd()}")
print(f"PATH: {os.environ.get('PATH', 'Not set')}")

try:
    from mcp.server.fastmcp import FastMCP, Context
    print("SUCCESS: MCP modules imported successfully!")
except ImportError as e:
    print(f"ERROR: Failed to import MCP modules: {e}")
    import mcp
    print(f"MCP module location: {mcp.__file__}")
