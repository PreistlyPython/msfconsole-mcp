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
