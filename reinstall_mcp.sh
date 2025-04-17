#!/bin/bash

# Script to reinstall the MCP environment correctly
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Reinstalling MCP environment ==="

# Check if virtualenv is installed
if ! command -v virtualenv &> /dev/null; then
    echo "Installing virtualenv..."
    pip install virtualenv
fi

# Remove existing virtual environment if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create a fresh virtual environment
echo "Creating new virtual environment..."
virtualenv venv

# Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install -U pip
pip install -U wheel
pip install -r requirements.txt

# Explicitly install MCP with all components
echo "Installing MCP package..."
pip install -U "mcp[cli]>=0.1.0"
pip install -U "typing-extensions>=4.0.0"

# Verify installation
echo "Verifying MCP installation..."
python -c "from mcp.server.fastmcp import FastMCP, Context; print('MCP successfully installed!')"

echo "=== Installation complete ==="
echo "You can now start the MCP server with: ./start_mcp.sh"
