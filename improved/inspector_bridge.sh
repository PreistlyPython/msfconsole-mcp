#!/usr/bin/bash

# MCP Inspector Bridge for Improved Metasploit MCP
# This script acts as a bridge between the MCP Inspector and our improved Metasploit MCP

# Function for logging to stderr
log_stderr() {
    echo "[Bridge] $1" >&2
}

# Display helpful information
log_stderr "Starting MCP Inspector Bridge for Improved Metasploit MCP"
log_stderr "-------------------------------------------------------"

# Set correct environment variables
export PYTHONPATH="/home/dell/coding/mcp:/home/dell/coding/mcp/msfconsole:/home/dell/coding/mcp/msfconsole/improved:$PYTHONPATH"

# Activate the virtual environment
source /home/dell/coding/mcp/msfconsole/venv/bin/activate || {
    log_stderr "Failed to activate virtual environment"
    exit 1
}

# Print debugging information
log_stderr "Python Version: $(python --version 2>&1)"
log_stderr "Virtual Environment: $(which python)"
log_stderr "PYTHONPATH: $PYTHONPATH"
log_stderr "Working Directory: $(pwd)"

# Change to the improved directory
cd /home/dell/coding/mcp/msfconsole/improved || {
    log_stderr "Failed to change directory to improved folder"
    exit 1
}

# Check if the main script exists
if [ ! -f "msfconsole_mcp_improved.py" ]; then
    log_stderr "Error: msfconsole_mcp_improved.py not found"
    exit 1
fi

# Make sure the script is executable
chmod +x msfconsole_mcp_improved.py

# Set environment variables to ensure MCP uses JSON for stdout
export MCP_DEBUG_TO_STDERR=1
export MCP_TRANSPORT=stdio
export MCP_STRICT_JSON=1

# Execute the Python script with specific arguments to ensure proper JSON handling
log_stderr "Launching Improved Metasploit MCP..."
exec python -u msfconsole_mcp_improved.py --json-stdout --strict-mode --debug-to-stderr
