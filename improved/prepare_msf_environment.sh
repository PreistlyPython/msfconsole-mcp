#!/bin/bash

# Script to prepare the Metasploit Framework environment
# This ensures the database is running before starting the MCP server

set -e

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

echo -e "${BOLD}${BLUE}==========================================${RESET}"
echo -e "${BOLD}${BLUE} Metasploit Framework Environment Setup${RESET}"
echo -e "${BOLD}${BLUE}==========================================${RESET}"

# Check for Metasploit
if ! command -v msfconsole &> /dev/null; then
    error "msfconsole not found in PATH."
    exit 1
else
    log "Found msfconsole: $(which msfconsole)"
fi

# Initialize Metasploit database
log "Checking Metasploit database status..."
DB_STATUS=$(msfdb status 2>&1)

if echo "$DB_STATUS" | grep -q "Database found, but is not running"; then
    warn "Metasploit database is not running. Initializing..."
    msfdb init
    success "Metasploit database initialized and started."
elif echo "$DB_STATUS" | grep -q "not found"; then
    warn "Metasploit database not found. Creating and initializing..."
    msfdb init
    success "Metasploit database created and started."
elif echo "$DB_STATUS" | grep -q "is running"; then
    success "Metasploit database is already running."
else
    warn "Unexpected database status: $DB_STATUS"
    warn "Attempting to initialize database..."
    msfdb init
fi

# Test database connection with a simple command
log "Testing database connection..."
TIMEOUT=10
timeout $TIMEOUT msfconsole -q -x "db_status; exit" || {
    error "Database connection test timed out after $TIMEOUT seconds."
    warn "This may indicate a problem with the database connection."
    warn "Continuing anyway, but the MCP might not work correctly."
}

log "Testing msfconsole basic functionality..."
SAMPLE_CMD_RESULT=$(timeout 15 msfconsole -q -x "version; exit" 2>/dev/null) || true

if echo "$SAMPLE_CMD_RESULT" | grep -q "Framework"; then
    success "msfconsole is functioning properly."
else
    warn "msfconsole test did not return expected output."
    warn "This may indicate a problem with Metasploit installation."
    warn "Continuing anyway, but the MCP might not work correctly."
fi

echo -e "${BOLD}${GREEN}==========================================${RESET}"
echo -e "${BOLD}${GREEN} Metasploit environment prepared successfully${RESET}"
echo -e "${BOLD}${GREEN}==========================================${RESET}"