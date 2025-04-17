#!/bin/bash
# Metasploit Framework MCP Setup Environment Script
# This script performs a complete clean setup of the msfconsole MCP environment

set -e  # Exit immediately if a command fails

echo "===============================================" 
echo "Starting MSFConsole MCP Environment Setup: $(date)"
echo "===============================================" 

# Set script variables
MCP_ROOT="/home/dell/coding/mcp"
MSFCONSOLE_DIR="$MCP_ROOT/msfconsole"
VENV_PATH="$MSFCONSOLE_DIR/venv"
DOCS_PATH="/home/dell/coding/documentation/msfconsole"
LOGS_DIR="$MSFCONSOLE_DIR/logs"

echo "MCP_ROOT: $MCP_ROOT"
echo "MSFCONSOLE_DIR: $MSFCONSOLE_DIR"
echo "VENV_PATH: $VENV_PATH"
echo "DOCS_PATH: $DOCS_PATH"
echo "LOGS_DIR: $LOGS_DIR"

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p "$DOCS_PATH"
mkdir -p "$LOGS_DIR"

# Go to the project directory
cd "$MSFCONSOLE_DIR"

# Check if Metasploit is installed
if ! command -v msfconsole &> /dev/null; then
    echo "WARNING: msfconsole not found in PATH."
    echo "The MCP requires Metasploit Framework to be installed."
    echo "Would you like to attempt to install it? (y/n)"
    read -r install_msf
    
    if [[ "$install_msf" == "y" ]]; then
        echo "Attempting to install Metasploit Framework..."
        # This is a simple check - a production script would need more robust installation
        if command -v apt-get &> /dev/null; then
            sudo apt-get update
            sudo apt-get install -y metasploit-framework
        else
            echo "Automatic installation not supported on this platform."
            echo "Please install Metasploit Framework manually and run this script again."
            exit 1
        fi
    else
        echo "Proceeding without Metasploit Framework. Some functionality will be limited."
    fi
fi

# Remove old virtual environment if it exists
if [ -d "$VENV_PATH" ]; then
    echo "Removing old virtual environment..."
    rm -rf "$VENV_PATH"
fi

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv "$VENV_PATH"

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_PATH/bin/activate"

# Upgrade pip, setuptools, and wheel
echo "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install MCP and other requirements
echo "Installing MCP and other requirements..."
pip install --upgrade "mcp[cli]>=0.1.0" --verbose
pip install -U -r "$MSFCONSOLE_DIR/requirements.txt"

# Check if the imports work
echo "Checking if MCP imports work..."
"$VENV_PATH/bin/python" "$MSFCONSOLE_DIR/test_mcp_import.py"

if [ $? -ne 0 ]; then
    echo "ERROR: MCP import test failed. The setup may still work, but there may be issues."
    echo "Trying system-wide installation as a fallback..."
    pip install --user "mcp[cli]>=0.1.0"
    "$VENV_PATH/bin/python" "$MSFCONSOLE_DIR/test_mcp_import.py"
    
    if [ $? -ne 0 ]; then
        echo "ERROR: System-wide installation also failed. Please check the error messages above."
        exit 1
    fi
fi

# Create a sample documentation file
if [ ! "$(ls -A "$DOCS_PATH")" ]; then
    echo "Creating a sample documentation file..."
    cat > "$DOCS_PATH/metasploit_cheatsheet.md" << EOF
# Metasploit Framework Cheatsheet

This is a sample documentation file for Metasploit Framework.

## Basic Commands

- msfconsole - Start the Metasploit console
- help - Display help information
- search [term] - Search for modules
- use [module] - Select a module to use
- show options - Display module options
- set [option] [value] - Set a module option
- exploit - Run the current module
- back - Move back from the current module
- exit - Exit the Metasploit console
EOF
fi

echo "===============================================" 
echo "MSFConsole MCP Environment Setup Complete!"
echo "===============================================" 
echo ""
echo "To start the MSFConsole MCP, run:"
echo "  ./launch_msfconsole_mcp.sh"
echo ""
