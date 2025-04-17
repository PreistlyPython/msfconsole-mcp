#!/bin/bash

# Enhanced Launch script for Improved MSFconsole MCP
# This script starts the MSFconsole MCP with proper environment settings and database initialization

set -e

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory if it doesn't exist
mkdir -p logs

# Log file
LOG_FILE="logs/msfconsole_mcp_launcher_$(date +%Y%m%d_%H%M%S).log"

# Enable logging
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# Color and formatting
BOLD="\e[1m"
RESET="\e[0m"
BLUE="\e[34m"
GREEN="\e[32m"
RED="\e[31m"
YELLOW="\e[33m"

# Log functions
log() { echo -e "${BLUE}[INFO]${RESET} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${RESET} $1"; }
error() { echo -e "${RED}[ERROR]${RESET} $1"; }
warn() { echo -e "${YELLOW}[WARNING]${RESET} $1"; }

# Header
echo -e "${BOLD}${BLUE}==========================================${RESET}"
echo -e "${BOLD}${BLUE} Improved MSFConsole MCP Launcher${RESET}"
echo -e "${BOLD}${BLUE} $(date)${RESET}"
echo -e "${BOLD}${BLUE}==========================================${RESET}"
log "Working directory: $(pwd)"

# Check for Python virtual environment
if [ ! -d "../venv" ]; then
    error "Virtual environment not found."
    warn "Running the setup script first..."
    
    if [ -f "../fix_python_version.sh" ]; then
        bash ../fix_python_version.sh
    else
        error "fix_python_version.sh not found. Cannot set up environment."
        exit 1
    fi
fi

# Activate the virtual environment
source ../venv/bin/activate
log "Using Python: $(which python) ($(python --version))"

# Check Python version
PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
MAJOR_VERSION=$(echo "$PY_VERSION" | cut -d. -f1)
MINOR_VERSION=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$MAJOR_VERSION" != "3" ] || [ "$MINOR_VERSION" -lt 8 ]; then
    error "Incompatible Python version: $PY_VERSION. Need Python 3.8+."
    exit 1
fi

if [ "$MINOR_VERSION" -ge 11 ]; then
    warn "Python $PY_VERSION detected - will apply compatibility patches."
fi

# Add venv path to PYTHONPATH to ensure modules are found
VENV_SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
export PYTHONPATH="$SCRIPT_DIR:$VENV_SITE_PACKAGES:$PYTHONPATH"
log "PYTHONPATH set to: $PYTHONPATH"

# List installed packages
log "Installed packages (relevant):"
pip list | grep -E "mcp|typing-extensions|aiohttp|requests"

# Check if MCP can be imported
if ! python -c "import mcp.server.fastmcp" &>/dev/null; then
    error "Cannot import MCP. Installing requirements..."
    pip install -r ../requirements.txt
    
    # Check again
    if ! python -c "import mcp.server.fastmcp" &>/dev/null; then
        error "Still cannot import MCP. Please run ../fix_python_version.sh again."
        exit 1
    fi
fi

# Initialize Metasploit database first
echo -e "${BOLD}${BLUE}==========================================${RESET}"
echo -e "${BOLD}${BLUE} Preparing Metasploit Environment${RESET}"
echo -e "${BOLD}${BLUE}==========================================${RESET}"

if ! bash ./prepare_msf_environment.sh; then
    error "Failed to prepare Metasploit environment."
    warn "Continuing anyway, but some functionality may be limited."
fi

# Run the MCP server with proper error handling
echo -e "${BOLD}${BLUE}==========================================${RESET}"
echo -e "${BOLD}${BLUE} Starting Improved MSFConsole MCP server...${RESET}"
echo -e "${BOLD}${BLUE}==========================================${RESET}"

# Run with capturing output but allow Ctrl+C to work properly
if ! python -u msfconsole_mcp_improved.py; then
    error "Improved MSFConsole MCP failed to start. Check the logs for details."
    exit 1
fi
