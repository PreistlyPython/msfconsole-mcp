#!/bin/bash

# Enhanced fix_python_version.sh script for MSFConsole MCP
# This script sets up a proper Python environment for the MSFConsole MCP

set -e  # Exit on error

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Log function
log() {
    echo -e "\e[1;34m[INFO]\e[0m $1"
}

warn() {
    echo -e "\e[1;33m[WARNING]\e[0m $1"
}

error() {
    echo -e "\e[1;31m[ERROR]\e[0m $1"
}

success() {
    echo -e "\e[1;32m[SUCCESS]\e[0m $1"
}

# Create logs directory
mkdir -p logs

# Check for Python version compatibility
log "Checking Python versions..."

# Try to find a compatible Python version
PYTHON_CMD=""
for cmd in python3.8 python3.9 python3.10 python3 python; do
    if command -v $cmd &> /dev/null; then
        version=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        major=$(echo $version | cut -d. -f1)
        minor=$(echo $version | cut -d. -f2)
        
        if [[ "$major" == "3" && "$minor" -ge 8 && "$minor" -le 10 ]]; then
            PYTHON_CMD=$cmd
            log "Found compatible Python version: $($PYTHON_CMD --version)"
            break
        fi
    fi
done

if [[ -z "$PYTHON_CMD" ]]; then
    warn "Could not find an ideal Python version (3.8-3.10)"
    warn "Will try to use the current Python version, but it might have compatibility issues"
    PYTHON_CMD=$(command -v python3 || command -v python)
    log "Using: $($PYTHON_CMD --version)"
fi

# Backup existing virtual environment if it exists
if [[ -d "venv" ]]; then
    backup_dir="venv_backup_$(date +%Y%m%d%H%M%S)"
    log "Backing up existing virtual environment to $backup_dir"
    mv venv $backup_dir
fi

# Create a new virtual environment
log "Creating virtual environment with $($PYTHON_CMD --version)..."
$PYTHON_CMD -m venv venv

# Activate the virtual environment
source venv/bin/activate
log "Activated virtual environment: $(python --version)"

# Upgrade pip, setuptools, and wheel
log "Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install the requirements
log "Installing requirements..."
# Clean requirements.txt if it contains asyncio (it's part of standard library)
sed -i '/^asyncio/d' requirements.txt
pip install -r requirements.txt

# Check if MCP is properly installed
log "Verifying MCP installation..."
if python -c "import mcp.server.fastmcp" &> /dev/null; then
    success "MCP SDK imported successfully!"
else
    error "Failed to import MCP SDK. Installing again..."
    pip install "mcp[cli]>=0.1.0"
    
    # Check again
    if python -c "import mcp.server.fastmcp" &> /dev/null; then
        success "MCP SDK installed successfully!"
    else
        error "Failed to install MCP SDK. Please check your internet connection and try again."
        exit 1
    fi
fi

# Copy the config file
if [[ ! -f "config.py" ]] && [[ -f "${SCRIPT_DIR}/config.py.example" ]]; then
    log "Using example config.py file"
    cp "${SCRIPT_DIR}/config.py.example" "${SCRIPT_DIR}/config.py"
fi

# Fix PYTHONPATH
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
export PYTHONPATH="${SCRIPT_DIR}:${SITE_PACKAGES}:${PYTHONPATH}"
log "Set PYTHONPATH to: $PYTHONPATH"

# Final message
echo ""
success "Environment setup complete!"
echo ""
log "To activate this environment:"
echo "  source venv/bin/activate"
log "To run the MSFConsole MCP:"
echo "  python msfconsole_mcp.py"
echo ""
