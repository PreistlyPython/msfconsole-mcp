#!/usr/bin/bash

# Activate virtual environment
source /home/dell/coding/mcp/msfconsole/venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=/home/dell/coding/mcp:/home/dell/coding/mcp/msfconsole:$PYTHONPATH

# Print debug info
echo "Python: $(which python)"
echo "PYTHONPATH: $PYTHONPATH"

# Make sure the script is executable
chmod +x /home/dell/coding/mcp/msfconsole/msfconsole_mcp.py

# Go to the directory and run the server
cd /home/dell/coding/mcp/msfconsole
exec python -u msfconsole_mcp.py
