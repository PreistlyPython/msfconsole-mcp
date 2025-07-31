#!/bin/bash

# Enhanced MCP launcher for Claude Desktop
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Source Metasploit environment if available
if [ -f "msf_environment.env" ]; then
    source msf_environment.env
fi

# Activate virtual environment
source venv_enhanced/bin/activate

# Set environment variables
export MSF_MCP_ENVIRONMENT="development"
export MSF_LOG_LEVEL="INFO" 
export MSF_RPC_HOST="127.0.0.1"
export MSF_RPC_PORT="55552"
export MSF_SECURITY_AUDIT_LOGGING="true"
export MSF_PERFORMANCE_CACHE_ENABLED="true"
export PYTHONPATH="$SCRIPT_DIR"
export PYTHONUNBUFFERED="1"

# Ensure Metasploit paths are in PATH
export PATH="/opt/metasploit-framework/bin:/usr/bin:$PATH"

# Launch the enhanced MCP server with the virtual environment's Python
exec "$SCRIPT_DIR/venv_enhanced/bin/python" msfconsole_mcp_enhanced.py