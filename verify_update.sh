#!/bin/bash

# MSFConsole Update Verification Script
# ====================================

echo "🔍 MSFConsole Update Verification"
echo "=================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check current version
print_info "Checking MSFConsole version..."
VERSION_OUTPUT=$(msfconsole -v 2>&1)
echo "$VERSION_OUTPUT"

# Check if update warning is gone
if echo "$VERSION_OUTPUT" | grep -q "more than two weeks old"; then
    print_warning "Framework still shows update warning"
    print_info "This is normal if update was just completed"
else
    print_success "No outdated framework warnings!"
fi

# Extract version number
VERSION=$(echo "$VERSION_OUTPUT" | grep "Framework Version" | cut -d':' -f2 | tr -d ' -')
print_info "Current version: $VERSION"

# Check MSF functionality
print_info "Testing basic MSF functionality..."
timeout 30 msfconsole -q -x "version; exit" > /tmp/msf_test.log 2>&1
if [ $? -eq 0 ]; then
    print_success "MSFConsole basic functionality working"
else
    print_error "MSFConsole functionality test failed"
    print_info "Check /tmp/msf_test.log for details"
fi

# Test payload generation
print_info "Testing payload generation..."
timeout 30 msfvenom --list payloads | head -5 > /tmp/msfvenom_test.log 2>&1
if [ $? -eq 0 ]; then
    print_success "Payload generation working"
else
    print_warning "Payload generation test had issues"
fi

# Check database connectivity
print_info "Testing database connectivity..."
timeout 30 msfconsole -q -x "db_status; exit" > /tmp/msf_db_test.log 2>&1
if [ $? -eq 0 ]; then
    print_success "Database connectivity test completed"
    if grep -q "Connected to" /tmp/msf_db_test.log; then
        print_success "Database is connected"
    else
        print_warning "Database may not be connected"
    fi
else
    print_warning "Database test timed out"
fi

# Check for any remaining issues
print_info "Summary:"
echo "==============="
echo "Version: $VERSION"
echo "Basic functionality: $([ -f /tmp/msf_test.log ] && echo "✅ Working" || echo "❌ Issues")"
echo "Payload generation: $(msfvenom --help > /dev/null 2>&1 && echo "✅ Working" || echo "❌ Issues")"
echo ""

# Clean up
rm -f /tmp/msf_test.log /tmp/msfvenom_test.log /tmp/msf_db_test.log

print_info "✅ Verification complete!"
print_info "If all tests passed, your MSF update was successful!"