#!/bin/bash

# Comprehensive Metasploit Environment Setup
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

# Function to check if running with proper permissions
check_permissions() {
    log_info "Checking permissions..."
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root - some operations may require non-root user"
    else
        log_info "Running as user: $(whoami)"
    fi
}

# Function to check Metasploit installation
check_metasploit() {
    log_info "Checking Metasploit Framework installation..."
    
    # Check for msfconsole
    if command -v msfconsole &> /dev/null; then
        MSF_VERSION=$(msfconsole --version 2>/dev/null | head -n1 || echo "Unknown version")
        log_success "msfconsole found: $MSF_VERSION"
        log_info "Location: $(which msfconsole)"
    else
        log_error "msfconsole not found!"
        return 1
    fi
    
    # Check for msfvenom
    if command -v msfvenom &> /dev/null; then
        log_success "msfvenom found: $(which msfvenom)"
    else
        log_warning "msfvenom not found!"
    fi
    
    # Check for msfrpcd
    if command -v msfrpcd &> /dev/null; then
        log_success "msfrpcd found: $(which msfrpcd)"
    else
        log_warning "msfrpcd not found - RPC mode will not work"
    fi
    
    return 0
}

# Function to check database
check_database() {
    log_info "Checking Metasploit database..."
    
    # Check if msfdb command exists
    if command -v msfdb &> /dev/null; then
        log_success "msfdb command found"
        
        # Check database status
        DB_STATUS=$(msfdb status 2>/dev/null || echo "unknown")
        if echo "$DB_STATUS" | grep -q "started"; then
            log_success "Metasploit database is running"
        else
            log_warning "Metasploit database is not running"
            log_info "Database status: $DB_STATUS"
            
            # Try to start database (non-interactive)
            log_info "Attempting to initialize database..."
            if msfdb init --no-user-prompt &>/dev/null; then
                log_success "Database initialized"
            else
                log_warning "Could not initialize database automatically"
            fi
        fi
    else
        log_warning "msfdb command not found - database management limited"
    fi
}

# Function to test basic functionality
test_basic_functionality() {
    log_info "Testing basic Metasploit functionality..."
    
    # Test msfconsole version
    if msfconsole --version &>/dev/null; then
        log_success "msfconsole version check passed"
    else
        log_error "msfconsole version check failed"
        return 1
    fi
    
    # Test simple msfconsole command
    log_info "Testing simple msfconsole command..."
    if echo "version; exit" | timeout 30 msfconsole -q &>/dev/null; then
        log_success "Basic msfconsole command test passed"
    else
        log_warning "Basic msfconsole command test failed (may be slow startup)"
    fi
    
    # Test msfvenom
    if command -v msfvenom &> /dev/null; then
        if msfvenom --help &>/dev/null; then
            log_success "msfvenom functionality test passed"
        else
            log_warning "msfvenom functionality test failed"
        fi
    fi
    
    return 0
}

# Function to setup proper directories and permissions
setup_directories() {
    log_info "Setting up directories and permissions..."
    
    # Create necessary directories
    mkdir -p /tmp/msf_workspaces
    mkdir -p /tmp/msf_scripts
    mkdir -p logs
    
    # Set proper permissions
    chmod 755 /tmp/msf_workspaces
    chmod 755 /tmp/msf_scripts
    chmod 755 logs
    
    log_success "Directories created and permissions set"
}

# Function to create test resource script
create_test_script() {
    log_info "Creating test resource script..."
    
    cat > /tmp/msf_test.rc << 'EOF'
# Test resource script for MSF MCP
version
help
exit
EOF
    
    chmod 644 /tmp/msf_test.rc
    log_success "Test resource script created at /tmp/msf_test.rc"
}

# Function to test resource script execution
test_resource_script() {
    log_info "Testing resource script execution..."
    
    if [ -f "/tmp/msf_test.rc" ]; then
        if timeout 30 msfconsole -q -r /tmp/msf_test.rc &>/dev/null; then
            log_success "Resource script execution test passed"
            rm -f /tmp/msf_test.rc
        else
            log_warning "Resource script execution test failed"
        fi
    else
        log_warning "Test resource script not found"
    fi
}

# Function to check and fix PATH issues
check_path() {
    log_info "Checking PATH configuration..."
    
    # Check if Metasploit binaries are in PATH
    MSF_PATHS=("/usr/bin" "/opt/metasploit-framework/bin" "/usr/share/metasploit-framework")
    
    for path in "${MSF_PATHS[@]}"; do
        if [ -d "$path" ]; then
            log_info "Found Metasploit directory: $path"
            if [[ ":$PATH:" != *":$path:"* ]]; then
                log_warning "$path not in PATH"
                export PATH="$path:$PATH"
                log_info "Added $path to PATH for this session"
            fi
        fi
    done
}

# Function to check Ruby environment
check_ruby() {
    log_info "Checking Ruby environment..."
    
    if command -v ruby &> /dev/null; then
        RUBY_VERSION=$(ruby --version)
        log_success "Ruby found: $RUBY_VERSION"
    else
        log_warning "Ruby not found - may affect Metasploit functionality"
    fi
    
    # Check for bundler
    if command -v bundle &> /dev/null; then
        log_success "Bundler found"
    else
        log_warning "Bundler not found"
    fi
}

# Function to create environment file
create_env_file() {
    log_info "Creating environment configuration..."
    
    cat > msf_environment.env << EOF
# Metasploit Framework Environment Configuration
export MSF_ROOT=/usr/share/metasploit-framework
export MSF_DATABASE_CONFIG=/usr/share/metasploit-framework/config/database.yml
export METASPLOIT_FRAMEWORK_ROOT=/usr/share/metasploit-framework

# MCP Configuration
export MSF_MCP_ENVIRONMENT=development
export MSF_LOG_LEVEL=INFO
export MSF_RPC_HOST=127.0.0.1
export MSF_RPC_PORT=55552
export MSF_SECURITY_AUDIT_LOGGING=true
export MSF_PERFORMANCE_CACHE_ENABLED=true

# Python Configuration
export PYTHONPATH=$PWD
export PYTHONUNBUFFERED=1

# PATH Configuration
export PATH=/usr/bin:/opt/metasploit-framework/bin:\$PATH
EOF
    
    log_success "Environment file created: msf_environment.env"
}

# Function to test MCP integration
test_mcp_integration() {
    log_info "Testing MCP integration..."
    
    # Source environment
    if [ -f "msf_environment.env" ]; then
        source msf_environment.env
    fi
    
    # Test enhanced MCP startup
    if [ -f "venv_enhanced/bin/python" ]; then
        log_info "Testing enhanced MCP server startup..."
        if timeout 5 venv_enhanced/bin/python msfconsole_mcp_enhanced.py &>/dev/null; then
            log_success "Enhanced MCP server startup test passed"
        else
            log_warning "Enhanced MCP server startup test failed"
        fi
    else
        log_warning "Enhanced MCP virtual environment not found"
    fi
}

# Function to install missing components
install_missing_components() {
    log_info "Checking for missing components..."
    
    MISSING_PACKAGES=()
    
    # Check for essential packages
    if ! command -v postgresql &> /dev/null; then
        MISSING_PACKAGES+=("postgresql")
    fi
    
    if ! dpkg -l | grep -q metasploit-framework; then
        MISSING_PACKAGES+=("metasploit-framework")
    fi
    
    if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
        log_warning "Missing packages detected: ${MISSING_PACKAGES[*]}"
        log_info "To install missing packages, run:"
        log_info "sudo apt update && sudo apt install -y ${MISSING_PACKAGES[*]}"
    else
        log_success "All essential packages appear to be installed"
    fi
}

# Main execution function
main() {
    echo "=================================================="
    echo "      Metasploit Environment Setup & Test"
    echo "=================================================="
    
    check_permissions
    check_path
    check_ruby
    install_missing_components
    
    if check_metasploit; then
        log_success "Metasploit Framework is properly installed"
        
        check_database
        setup_directories
        create_test_script
        test_resource_script
        test_basic_functionality
        create_env_file
        test_mcp_integration
        
        echo ""
        log_success "Environment setup completed!"
        echo ""
        log_info "To use the enhanced environment:"
        log_info "1. source msf_environment.env"
        log_info "2. ./launch_mcp_for_claude.sh"
        echo ""
        log_info "Or restart Claude Desktop to load the enhanced MCP"
        
    else
        log_error "Metasploit Framework installation issues detected"
        echo ""
        log_info "To install Metasploit Framework:"
        log_info "1. sudo apt update"
        log_info "2. sudo apt install -y metasploit-framework"
        log_info "3. sudo msfdb init"
        echo ""
        return 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    "check")
        check_metasploit && check_database
        ;;
    "test")
        test_basic_functionality
        ;;
    "env")
        create_env_file
        ;;
    *)
        main
        ;;
esac