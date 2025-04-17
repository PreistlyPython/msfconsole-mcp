#!/bin/bash

# Quick Fix Script for MSFconsole MCP
# This script ensures the environment is correctly set up before running the MCP

set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "===================================================="
echo "MSFconsole MCP Quick Fix and Launcher"
echo "===================================================="
echo "Working directory: $(pwd)"

# Create logs directory
mkdir -p logs

# Check and activate virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Get site-packages path
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
echo "Found site-packages directory: $SITE_PACKAGES"

# Set up PYTHONPATH correctly
export PYTHONPATH="$SITE_PACKAGES:$PYTHONPATH"
echo "PYTHONPATH set to: $PYTHONPATH"

# Verify MCP installation
echo "Verifying MCP installation..."
if ! python -c "import mcp.server.fastmcp" 2>/dev/null; then
    echo "MCP not properly installed. Installing required packages..."
    pip install -r requirements.txt
    pip install "mcp[cli]>=0.1.0"
fi

# Set proper permissions
echo "Setting executable permissions on scripts..."
chmod +x msfconsole_mcp.py launch_msfconsole_mcp.sh check_mcp_environment.py

# Run environment check to verify everything is working
echo "Running environment check..."
./check_mcp_environment.py

# Ask user whether to continue
echo ""
echo "Do you want to run the MCP now? (y/n)"
read -r response
if [[ "$response" =~ ^[Yy]$ ]]; then
    echo "Starting MSFconsole MCP..."
    python -u msfconsole_mcp.py
else
    echo "To run the MCP manually, use: ./launch_msfconsole_mcp.sh"
    echo "Environment is now properly set up."
fi
