#!/usr/bin/bash

# MCP Inspector Bridge for Improved Metasploit MCP
# This script acts as a bridge between the MCP Inspector and our improved Metasploit MCP

# Redirect all non-JSON output to stderr instead of stdout
# This is critical for the MCP protocol which expects only valid JSON on stdout

# Display helpful information to stderr
echo "Starting MCP Inspector Bridge for Improved Metasploit MCP" >&2
echo "-------------------------------------------------------" >&2

# Set correct environment variables
export PYTHONPATH="/home/dell/coding/mcp:/home/dell/coding/mcp/msfconsole:/home/dell/coding/mcp/msfconsole/improved:$PYTHONPATH"
export MCP_TRANSPORT="stdio"
export MCP_DEBUG="1"

# Print PID for debugging
echo "Bridge PID: $$" >&2

# Activate the virtual environment
source /home/dell/coding/mcp/msfconsole/venv/bin/activate 2>&1 || {
    echo "Failed to activate virtual environment" >&2
    exit 1
}

# Print debugging information to stderr
echo "Python Version: $(python --version 2>&1)" >&2
echo "Virtual Environment: $(which python 2>&1)" >&2
echo "PYTHONPATH: $PYTHONPATH" >&2
echo "Working Directory: $(pwd)" >&2

# Change to the improved directory
cd /home/dell/coding/mcp/msfconsole/improved 2>&1

# Check if the main script exists
if [ ! -f "msfconsole_mcp_improved.py" ]; then
    echo "Error: msfconsole_mcp_improved.py not found" >&2
    exit 1
fi

# Make sure the script is executable
chmod +x msfconsole_mcp_improved.py 2>&1

# Create a temporary FIFO to handle stdout from the python script properly
FIFO_PATH=$(mktemp -u)
mkfifo $FIFO_PATH
# Clean up on exit
trap "rm -f $FIFO_PATH" EXIT

# Function to validate and filter JSON
filter_valid_json() {
    while IFS= read -r line; do
        # Test if line is valid JSON before passing it through
        if echo "$line" | python -c "import sys,json; json.loads(sys.stdin.read())" &>/dev/null; then
            echo "$line"
        else
            echo "Invalid JSON skipped: $line" >&2
        fi
    done
}

# Launch the Python script with proper output handling
echo "Launching Improved Metasploit MCP..." >&2

# Start the filter in background
cat $FIFO_PATH | filter_valid_json &
FILTER_PID=$!

# Start the actual script
python msfconsole_mcp_improved.py >$FIFO_PATH 2>&2

EXIT_CODE=$?
wait $FILTER_PID
exit $EXIT_CODE
