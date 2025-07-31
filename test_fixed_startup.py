#!/usr/bin/env python3
"""Test the fixed startup script"""

import subprocess
import json
import time

def test_startup():
    print("Testing fixed startup script...")
    
    # Start the MCP server
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Give it a moment to start
        time.sleep(5)
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            },
            "id": 1
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        print(f"Response: {response_line}")
        
        # Check if it's valid JSON
        try:
            response = json.loads(response_line)
            print("✅ Valid JSON response received!")
            if "result" in response and "serverInfo" in response["result"]:
                print(f"✅ Server: {response['result']['serverInfo']['name']}")
                process.terminate()
                return True
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
            print(f"Raw response: {repr(response_line)}")
            
            # Check stderr for any issues
            stderr_output = process.stderr.read()
            if stderr_output:
                print(f"Stderr: {stderr_output}")
            return False
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        process.terminate()
        return False

if __name__ == "__main__":
    success = test_startup()
    print(f"Test {'PASSED' if success else 'FAILED'}")