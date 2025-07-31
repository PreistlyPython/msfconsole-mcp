#!/usr/bin/env python3
"""Test get_msf_status tool with proper initialization"""

import json
import subprocess
import time

def test_status_with_proper_init():
    print("🔍 Testing get_msf_status with proper initialization")
    print("=" * 60)
    
    # Start the MCP server
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        print("⏳ Waiting for server startup...")
        time.sleep(8)  # Longer startup delay
        
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
        
        print("📤 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read init response
        init_response_line = process.stdout.readline()
        print(f"📥 Init response: {init_response_line.strip()}")
        init_response = json.loads(init_response_line)
        print(f"✅ Server initialized: {init_response.get('result', {}).get('serverInfo', {}).get('name')}")
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        print("📤 Sending initialized notification...")
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
        
        # Give it a moment to process
        time.sleep(2)
        
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
        
        # Read status response
        print("📥 Waiting for status response...")
        status_response_line = process.stdout.readline()
        print(f"📥 Status response: {status_response_line.strip()}")
        
        if status_response_line:
            status_response = json.loads(status_response_line)
            print(f"📊 Parsed response:")
            print(json.dumps(status_response, indent=2))
            
            if "result" in status_response and "content" in status_response["result"]:
                print("✅ Tool executed successfully")
                content = json.loads(status_response["result"]["content"][0]["text"])
                print(f"📋 Status: {content.get('status')}")
                return True
            elif "error" in status_response:
                print(f"❌ Tool returned error: {status_response['error']}")
                return False
        else:
            print("❌ No response received")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        process.terminate()
        # Check stderr for any errors
        stderr_output = process.stderr.read()
        if stderr_output:
            print(f"\n📝 Stderr output:\n{stderr_output}")

if __name__ == "__main__":
    success = test_status_with_proper_init()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")