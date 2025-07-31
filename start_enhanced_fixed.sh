#!/bin/bash

# Enhanced MCP with fixes launcher
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Redirect all initialization output to stderr to avoid breaking JSON protocol
{
    echo "🚀 Starting Enhanced Metasploit MCP with fixes..."
    
    # Initialize Metasploit database first
    echo "📊 Checking database status..."
    msfdb status || true
    
    # Test initialization
    echo "🧪 Testing initialization..."
    python3 msf_init.py
    
    echo "🔧 Starting MCP server..."
} >&2

# Set required environment variables for Metasploit
export HOME=${HOME:-/home/dell}
export PATH="/opt/metasploit-framework/bin:/usr/bin:$PATH"

# Launch the enhanced MCP server (stdout must be clean for JSON protocol)
exec "$SCRIPT_DIR/venv_enhanced/bin/python" msfconsole_mcp_enhanced.py