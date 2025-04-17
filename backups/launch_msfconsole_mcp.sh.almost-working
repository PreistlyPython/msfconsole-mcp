#!/bin/bash

# Launch script for MSFconsole MCP
# This script starts the MSFconsole MCP with proper environment settings

set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Check for Python virtual environment
if [ ! -d "venv" ]; then
    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Make sure MCP requirements are installed
if ! pip list | grep -q "^mcp "; then
    echo "MCP SDK not found. Installing requirements..."
    pip install -r requirements.txt
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Run test to verify MCP imports
echo "Testing MCP imports..."
python3 test_mcp_import.py

# Check if safe_context.py exists
if [ ! -f "safe_context.py" ]; then
    echo "ERROR: safe_context.py not found. Please make sure it exists in the current directory."
    exit 1
fi

# Run the MCP server
echo "Starting MSFconsole MCP server..."
LOG_FILE="logs/msfconsole_mcp_$(date +%Y%m%d_%H%M%S).log"
python3 msfconsole_mcp.py | tee "$LOG_FILE"
