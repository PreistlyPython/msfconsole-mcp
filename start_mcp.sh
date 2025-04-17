#!/bin/bash

# Script to start the Metasploit Console MCP server

echo "Starting Metasploit Console MCP server..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3 and try again."
    exit 1
fi

# Activate the virtual environment
SOURCE_DIR="$(dirname "${BASH_SOURCE[0]}")"
if [ -d "$SOURCE_DIR/venv/bin" ]; then
    echo "Activating virtual environment..."
    source "$SOURCE_DIR/venv/bin/activate"
fi

# Check if the installation is complete
if ! python3 -c "import mcp.server.fastmcp" &> /dev/null; then
    echo "Error: MCP SDK is not installed."
    echo "Please run './install.sh' to install dependencies."
    exit 1
fi

# Start the MCP server
echo "Starting server with full debug output..."
python3 "$SOURCE_DIR/msfconsole_mcp.py" "$@" 2>&1
