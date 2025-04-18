#!/usr/bin/bash

# =================================================================
# MCP Inspector Bridge for Improved Metasploit MCP Server
# =================================================================
# This script acts as a bridge between the MCP Inspector and our 
# improved Metasploit MCP implementation, ensuring that only valid
# JSON-RPC 2.0 protocol messages are passed to stdout.
# =================================================================

# Function to log messages to stderr only for debugging
log_stderr() {
    echo "[Bridge] $1" >&2
}

# Display helpful information to stderr only
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
if [ -f "/home/dell/coding/mcp/msfconsole/venv/bin/activate" ]; then
    source /home/dell/coding/mcp/msfconsole/venv/bin/activate
    log_stderr "Virtual environment activated successfully"
else
    log_stderr "ERROR: Virtual environment not found"
    exit 1
fi

# Create a debug log
DEBUG_LOG="/tmp/mcp_bridge_$(date +%Y%m%d_%H%M%S).log"
log_stderr "Logging debug output to $DEBUG_LOG"

# Change to the improved directory
cd /home/dell/coding/mcp/msfconsole/improved || {
    log_stderr "Failed to change directory"
    exit 1
}

# Create a temporary named pipe for JSON filtering
FIFO_PATH=$(mktemp -u)
mkfifo "$FIFO_PATH"
log_stderr "Created JSON filter FIFO at $FIFO_PATH"

# Clean up on exit - remove the FIFO
cleanup() {
    log_stderr "Cleaning up resources..."
    rm -f "$FIFO_PATH"
}
trap cleanup EXIT INT TERM

# Ensure path to Python is absolute
PYTHON_PATH=$(which python)
log_stderr "Using Python at: $PYTHON_PATH"

# Function to validate and filter JSON - only passes valid JSON-RPC 2.0 messages
# Function to validate and filter JSON - only passes valid JSON-RPC 2.0 messages
filter_valid_json() {
    log_stderr "JSON filter started"
    while IFS= read -r line; do
        # Skip empty lines or lines with only whitespace
        if [ -z "$(echo "$line" | tr -d '[:space:]')" ]; then
            continue
        fi
        
        # Test if line is valid JSON before passing it through
        if echo "$line" | "$PYTHON_PATH" -c "import sys,json; json.loads(sys.stdin.read())" &>/dev/null; then
            # Check if it's a valid JSON-RPC 2.0 message (contains jsonrpc field)
            if echo "$line" | "$PYTHON_PATH" -c "import sys,json; obj=json.loads(sys.stdin.read()); sys.exit(0 if 'jsonrpc' in obj and obj['jsonrpc'] == '2.0' else 1)" &>/dev/null; then
                # Valid JSON-RPC message - output to stdout with added newline to ensure proper separation
                echo "$line"
                log_stderr "Passed valid JSON-RPC message: ${line:0:50}..."
            else
                # Valid JSON but not a JSON-RPC message
                log_stderr "Filtered non-RPC JSON: ${line:0:50}..."
            fi
        else
            # Not valid JSON - log to stderr
            log_stderr "Filtered invalid JSON: ${line:0:50}..."
        fi
    done
}
..." >> "$DEBUG_LOG"
            else
                # Valid JSON but not a JSON-RPC message
                echo "Filtered non-RPC JSON: ${line:0:50}..." >> "$DEBUG_LOG"
            fi
        else
            # Not valid JSON - log to stderr
            echo "Filtered invalid JSON: ${line:0:50}..." >> "$DEBUG_LOG"
        fi
    done
}

# Set environment variables for MCP
export MCP_DEBUG=1
export MCP_DEBUG_TO_STDERR=1
export MCP_TRANSPORT=stdio
export MCP_JSON_STDOUT=1
export MCP_STRICT_MODE=1

# Start the filter in background, reading from the FIFO
cat "$FIFO_PATH" | filter_valid_json &
FILTER_PID=$!

log_stderr "Launching Improved Metasploit MCP..."

# Execute with stdout to the FIFO (for filtering) and stderr directly to debug log
"$PYTHON_PATH" -u msfconsole_mcp_improved.py \
    --json-stdout \
    --strict-mode \
    --debug-to-stderr > "$FIFO_PATH" 2> >(tee -a "$DEBUG_LOG" >&2)

# Save exit code
EXIT_CODE=$?
log_stderr "MCP process exited with code: $EXIT_CODE"

# Log the last few lines of debug output
log_stderr "Last 10 lines of debug log:"
tail -n 10 "$DEBUG_LOG" | while IFS= read -r line; do
    log_stderr "  $line"
done

# Wait for filter to finish
wait $FILTER_PID 2>/dev/null || true

# Exit with the original exit code
exit $EXIT_CODE
