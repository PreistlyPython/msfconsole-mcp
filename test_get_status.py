#!/usr/bin/env python3
"""Test the get_msf_status tool specifically"""

import json
import subprocess
import time

def test_get_status():
    print("🔍 Testing get_msf_status tool specifically")
    print("=" * 50)
    
    # Start the MCP server
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        time.sleep(5)  # Allow startup
        
        # Initialize
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
        
        # Read init response
        init_response = json.loads(process.stdout.readline())
        print(f"✅ Initialize response: {init_response.get('result', {}).get('serverInfo', {}).get('name')}")
        
        # Test get_msf_status tool
        status_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "get_msf_status",
                "arguments": {}
            },
            "id": 2
        }
        
        print(f"📤 Sending get_msf_status request...")
        process.stdin.write(json.dumps(status_request) + "\n")
        process.stdin.flush()
        
        # Read status response with timeout
        print("📥 Waiting for response...")
        try:
            # Set up a timeout for reading
            response_line = process.stdout.readline()
            if response_line:
                status_response = json.loads(response_line)
                print(f"✅ Status response received:")
                print(json.dumps(status_response, indent=2))
                
                if "result" in status_response:
                    print("✅ Tool executed successfully")
                    return True
                elif "error" in status_response:
                    print(f"❌ Tool returned error: {status_response['error']}")
                    return False
            else:
                print("❌ No response received")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"Raw response: {repr(response_line)}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        process.terminate()
        # Check stderr for any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"Stderr: {stderr_output}")

if __name__ == "__main__":
    success = test_get_status()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")