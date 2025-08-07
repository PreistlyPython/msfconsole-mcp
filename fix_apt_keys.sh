#!/bin/bash

# Fix APT Repository Key Issues
# =============================

set -e

echo "🔧 Fixing APT Repository Key Issues"
echo "==================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root or with sudo"
   exit 1
fi

# Fix Docker GPG key
print_info "Fixing Docker repository key..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

# Fix Metasploit GPG key
print_info "Fixing Metasploit repository key..."
curl -fsSL https://apt.metasploit.com/metasploit-framework.gpg.key | apt-key add - || {
    print_warning "Traditional apt-key method failed, trying modern approach..."
    curl -fsSL https://apt.metasploit.com/metasploit-framework.gpg.key | gpg --dearmor -o /usr/share/keyrings/metasploit-archive-keyring.gpg
    # Update the sources.list entry to use the new key
    sed -i 's|deb https://apt.metasploit.com|deb [signed-by=/usr/share/keyrings/metasploit-archive-keyring.gpg] https://apt.metasploit.com|g' /etc/apt/sources.list.d/metasploit-framework.list 2>/dev/null || true
}

# Remove/comment out the problematic TimescaleDB PPA
print_info "Handling TimescaleDB PPA issue..."
if [ -f /etc/apt/sources.list.d/timescale-ubuntu-timescaledb-ppa-noble.list ]; then
    print_warning "Disabling TimescaleDB PPA (not available for Ubuntu Noble)..."
    mv /etc/apt/sources.list.d/timescale-ubuntu-timescaledb-ppa-noble.list /etc/apt/sources.list.d/timescale-ubuntu-timescaledb-ppa-noble.list.disabled
    print_info "TimescaleDB PPA disabled"
fi

# Alternative: Comment out the PPA in sources.list
sed -i '/timescale\/timescaledb-ppa/s/^/# /' /etc/apt/sources.list 2>/dev/null || true
sed -i '/timescale\/timescaledb-ppa/s/^/# /' /etc/apt/sources.list.d/*.list 2>/dev/null || true

# Update package lists
print_info "Updating package lists..."
apt update 2>&1 | grep -E "^W:|^E:" || print_info "Package lists updated successfully"

# Show status
echo ""
print_info "✅ Repository key fixes applied!"
print_info "You can now proceed with the MSF update"

# Optional: Install missing GPG keys automatically
print_info "Checking for any remaining missing keys..."
apt update 2>&1 | grep "NO_PUBKEY" | while read -r line; do
    key=$(echo $line | grep -oP 'NO_PUBKEY \K[A-F0-9]+')
    if [ ! -z "$key" ]; then
        print_warning "Found missing key: $key"
        print_info "Attempting to retrieve key from keyserver..."
        apt-key adv --keyserver keyserver.ubuntu.com --recv-keys $key || \
        apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys $key || \
        print_error "Failed to retrieve key $key"
    fi
done

echo ""
echo "🎯 Next Steps:"
echo "1. Run the MSF update: sudo /home/dell/coding/mcp/msfconsole/update_msfconsole.sh"
echo "2. Or update MSF directly: sudo msfupdate"
echo ""
echo "Note: The warnings were about:"
echo "- Docker repository key (fixed)"
echo "- Metasploit repository key (fixed)"
echo "- TimescaleDB PPA not available for Ubuntu Noble (disabled)"