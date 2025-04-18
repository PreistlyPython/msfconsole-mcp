#!/usr/bin/bash

# ================================================================
# MCP-Server-MSFconsole Update and Restart Script
# ================================================================
# This script applies all the fixes and improvements to the 
# MCP-Server-MSFconsole integration and restarts the service.
# ================================================================

set -e  # Exit on any error

echo "==================================================================="
echo "MCP-Server-MSFconsole Improved - Update and Restart"
echo "==================================================================="

# Change to the improved directory
cd "$(dirname "$0")"
echo "[1/5] Changed to directory: $(pwd)"

# Backup original files
echo "[2/5] Creating backups of original files..."
cp -f msfconsole_mcp_improved.py msfconsole_mcp_improved.py.bak.$(date +%Y%m%d%H%M%S)
cp -f inspector_bridge.sh inspector_bridge.sh.bak.$(date +%Y%m%d%H%M%S)
echo "      Backups created successfully."

# Ensure all script files are executable
echo "[3/5] Setting appropriate permissions..."
chmod +x msfconsole_mcp_improved.py
chmod +x inspector_bridge.sh
chmod +x json_filter.py

# Verify syntax of all modified files
echo "[4/5] Verifying syntax of all modified files..."
python3 -m py_compile msfconsole_mcp_improved.py
bash -n inspector_bridge.sh
python3 -m py_compile json_filter.py
echo "      All files passed syntax verification."

# Check if any instance of the server is running and kill it
echo "[5/5] Checking for running instances of MSFconsole MCP..."
if pgrep -f "msfconsole_mcp_improved.py" > /dev/null; then
    echo "      Found running instance. Stopping..."
    pkill -f "msfconsole_mcp_improved.py"
    sleep 2
    echo "      Instance stopped."
else
    echo "      No running instances found."
fi

echo "==================================================================="
echo "Update completed successfully!"
echo "==================================================================="
echo ""
echo "To start the MCP server, run:"
echo "./inspector_bridge.sh"
echo ""
echo "Or if you are integrating with Claude Desktop, ensure the server"
echo "is properly configured in Claude's MCP server settings."
echo "==================================================================="

exit 0
