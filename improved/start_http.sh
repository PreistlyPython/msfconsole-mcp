#!/bin/bash

# Set environment variables
export PYTHONPATH="/home/dell/coding/mcp/msfconsole:/home/dell/coding/mcp/msfconsole/improved:$PYTHONPATH"

# Activate virtual environment and run the server with HTTP
source /home/dell/coding/mcp/msfconsole/venv/bin/activate
cd /home/dell/coding/mcp/msfconsole/improved
python -m mcp.server.http --server msfconsole_mcp_improved:mcp --port 8000
