#!/bin/bash

# Enhanced MSF MCP Startup Script
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root (required for Metasploit)
check_permissions() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root. This is required for some Metasploit operations."
    else
        log_info "Running as non-root user: $(whoami)"
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not installed"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $PYTHON_VERSION"
    
    # Check Metasploit installation
    if ! command -v msfconsole &> /dev/null; then
        log_error "Metasploit Framework not found. Please install Metasploit."
        exit 1
    fi
    
    MSF_VERSION=$(msfconsole --version | head -n1)
    log_info "Metasploit version: $MSF_VERSION"
    
    # Check for msfrpcd
    if ! command -v msfrpcd &> /dev/null; then
        log_warning "msfrpcd not found in PATH. RPC mode may not work."
    fi
    
    log_success "System requirements check completed"
}

# Set up Python virtual environment
setup_venv() {
    log_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv_enhanced" ]; then
        python3 -m venv venv_enhanced
        log_success "Virtual environment created"
    else
        log_info "Virtual environment already exists"
    fi
    
    source venv_enhanced/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements_enhanced.txt" ]; then
        log_info "Installing Python dependencies..."
        pip install -r requirements_enhanced.txt
        log_success "Dependencies installed"
    else
        log_warning "requirements_enhanced.txt not found, installing minimal requirements"
        pip install mcp aiohttp PyYAML psutil
    fi
}

# Initialize configuration
setup_config() {
    log_info "Setting up configuration..."
    
    # Create default config if it doesn't exist
    if [ ! -f "msf_mcp_config.yaml" ]; then
        python3 -c "
from msf_config import ConfigurationManager
config_manager = ConfigurationManager('msf_mcp_config.yaml')
config_manager.create_default_config_file('msf_mcp_config.yaml')
print('Default configuration created')
"
        log_success "Default configuration created"
    else
        log_info "Configuration file already exists"
    fi
    
    # Create directories
    mkdir -p logs
    mkdir -p /tmp/msf_workspaces
    mkdir -p /tmp/msf_scripts
    
    log_success "Configuration setup completed"
}

# Check Metasploit database
check_database() {
    log_info "Checking Metasploit database..."
    
    # Try to check database status
    if command -v msfdb &> /dev/null; then
        if msfdb status | grep -q "started"; then
            log_success "Metasploit database is running"
        else
            log_warning "Metasploit database is not running"
            log_info "Starting Metasploit database..."
            sudo msfdb init
            sudo msfdb start
        fi
    else
        log_warning "msfdb command not found. Database management may be limited."
    fi
}

# Start the enhanced MCP server
start_server() {
    log_info "Starting Enhanced MSF MCP Server..."
    
    # Ensure virtual environment is activated
    source venv_enhanced/bin/activate
    
    # Set environment variables
    export MSF_MCP_ENVIRONMENT="development"
    export MSF_LOG_LEVEL="INFO"
    export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"
    
    # Start the server
    python3 msfconsole_mcp_enhanced.py
}

# Main execution
main() {
    log_info "Starting Enhanced Metasploit MCP Server Setup"
    log_info "============================================"
    
    check_permissions
    check_requirements
    setup_venv
    setup_config
    check_database
    
    log_success "Setup completed successfully!"
    log_info "Starting server..."
    
    start_server
}

# Handle script arguments
case "${1:-}" in
    "setup")
        check_permissions
        check_requirements
        setup_venv
        setup_config
        check_database
        log_success "Setup completed. Run './start_enhanced_mcp.sh' to start the server."
        ;;
    "start")
        start_server
        ;;
    "check")
        check_permissions
        check_requirements
        ;;
    *)
        main
        ;;
esac