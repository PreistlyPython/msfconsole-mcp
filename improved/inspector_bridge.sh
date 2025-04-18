#!/usr/bin/bash

# MCP Inspector Bridge for Improved Metasploit MCP
# This script acts as a bridge between the MCP Inspector and our improved Metasploit MCP

# Function to log messages to stderr only
log_stderr() {
    echo "[Bridge] $1" >&2
}

# Display helpful information to stderr only (not stdout)
log_stderr "Starting MCP Inspector Bridge for Improved Metasploit MCP"
log_stderr "-------------------------------------------------------"

# Set correct environment variables
export PYTHONPATH="/home/dell/coding/mcp:/home/dell/coding/mcp/msfconsole:/home/dell/coding/mcp/msfconsole/improved:$PYTHONPATH"

# Print debugging information to stderr only
log_stderr "Python Version: $(python --version 2>&1)"
log_stderr "Virtual Environment: $(which python)"
log_stderr "PYTHONPATH: $PYTHONPATH"
log_stderr "Working Directory: $(pwd)"

# Activate the virtual environment
source /home/dell/coding/mcp/msfconsole/venv/bin/activate 2>&1 || {
    log_stderr "Failed to activate virtual environment"
    exit 1
}

# Change to the improved directory
cd /home/dell/coding/mcp/msfconsole/improved 2>&1 || {
    log_stderr "Failed to change directory to improved folder"
    exit 1
}

# Check if the main script exists
if [ ! -f "msfconsole_mcp_improved.py" ]; then
    log_stderr "Error: msfconsole_mcp_improved.py not found"
    exit 1
}

# Make sure the script is executable
chmod +x msfconsole_mcp_improved.py 2>&1

# Create a temporary named pipe for filtering JSON
FIFO_PATH=$(mktemp -u)
mkfifo $FIFO_PATH
# Clean up on exit
trap "rm -f $FIFO_PATH" EXIT

# Function to validate and filter JSON
filter_valid_json() {
    log_stderr "JSON filter started"
    while IFS= read -r line; do
        # Skip empty lines
        if [ -z "$line" ]; then
            continue
        fi
        
        # Test if line is valid JSON before passing it through
        if echo "$line" | python -c "import sys,json; json.loads(sys.stdin.read())" &>/dev/null; then
            # Valid JSON - output to stdout
            echo "$line"
        else
            # Invalid JSON - log to stderr
            log_stderr "Invalid JSON filtered: ${line:0:50}..."
        fi
    done
}

# Set environment variables for proper MCP operation
export MCP_DEBUG=1
export MCP_DEBUG_TO_STDERR=1
export MCP_TRANSPORT=stdio

# Launch the Python script with proper output handling
log_stderr "Launching Improved Metasploit MCP..."

# Start the filter in background, reading from the FIFO
cat $FIFO_PATH | filter_valid_json &
FILTER_PID=$!

# Run the Python script with stdout redirected to the FIFO and stderr to stderr
python -u msfconsole_mcp_improved.py --json-stdout --strict-mode --debug-to-stderr >$FIFO_PATH 2>&2

# Save exit code and wait for filter to finish
EXIT_CODE=$?
wait $FILTER_PID

# Exit with the original exit code
exit $EXIT_CODE
