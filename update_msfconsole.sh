#!/bin/bash

# MSFConsole Framework Update Script
# Safely updates Metasploit Framework with proper error handling

set -e  # Exit on any error

echo "🔄 MSFConsole Framework Update Script"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root or with sudo
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root or with sudo"
   exit 1
fi

# Step 1: Pre-update checks
print_status "Step 1: Pre-update safety checks..."

# Get current version
CURRENT_VERSION=$(msfconsole -v 2>/dev/null | head -1 || echo "Unknown")
print_status "Current MSFConsole version: $CURRENT_VERSION"

# Check installation type
MSF_PATH="/opt/metasploit-framework"
if [[ ! -d "$MSF_PATH" ]]; then
    print_error "Metasploit Framework not found at $MSF_PATH"
    exit 1
fi

# Stop any running MSF processes
print_status "Stopping MSF processes..."
pkill -f msfconsole || true
sleep 2

# Stop PostgreSQL to prevent database corruption
print_status "Stopping PostgreSQL service..."
service postgresql stop || true
sleep 3

# Step 2: Create backup
BACKUP_DIR="/opt/metasploit-framework.backup.$(date +%Y%m%d_%H%M%S)"
print_status "Creating backup at $BACKUP_DIR..."
cp -r "$MSF_PATH" "$BACKUP_DIR"
print_status "Backup created successfully"

# Step 3: Execute update
print_status "Step 2: Executing framework update..."

# Try msfupdate
if [[ -f "$MSF_PATH/bin/msfupdate" ]]; then
    print_status "Using direct msfupdate..."
    "$MSF_PATH/bin/msfupdate" || {
        print_warning "Direct msfupdate failed, trying system msfupdate..."
        msfupdate || {
            print_error "Both msfupdate methods failed"
            exit 1
        }
    }
else
    print_status "Using system msfupdate..."
    msfupdate || {
        print_error "System msfupdate failed"
        exit 1
    }
fi

# Step 4: Post-update verification
print_status "Step 3: Post-update verification..."

# Restart PostgreSQL
print_status "Starting PostgreSQL service..."
service postgresql start
sleep 5

# Check new version
NEW_VERSION=$(msfconsole -v 2>/dev/null | head -1 || echo "Unknown")
print_status "Updated MSFConsole version: $NEW_VERSION"

# Test basic functionality
print_status "Testing MSFConsole functionality..."
timeout 30 msfconsole -q -x "version; exit" > /tmp/msf_test.log 2>&1 || {
    print_error "MSFConsole functionality test failed"
    cat /tmp/msf_test.log
    exit 1
}

# Initialize database if needed
print_status "Checking database status..."
msfdb init || print_warning "Database initialization had issues (may be normal)"

# Final status
print_status "✅ Update completed successfully!"
print_status "Previous version: $CURRENT_VERSION"
print_status "Current version:  $NEW_VERSION"
print_status "Backup location:  $BACKUP_DIR"

echo ""
echo "🎉 MSFConsole Framework has been updated!"
echo "💡 Restart any existing MSF sessions to use the new version"
echo "🔍 Test with: msfconsole -q -x 'version; exit'"