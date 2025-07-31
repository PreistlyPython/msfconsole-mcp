#!/usr/bin/env python3
"""Test get_msf_status tool with timeout handling"""

import json
import subprocess
import time
import threading
import queue

def read_responses(process, response_queue):
    """Read responses in a separate thread"""
    try:
        while True:
            line = process.stdout.readline()
            if not line:
                break
            response_queue.put(line.strip())
    except Exception as e:
        response_queue.put(f"ERROR: {e}")

def test_status_with_timeout():
    print("🔍 Testing get_msf_status with timeout handling")
    print("=" * 60)
    
    # Start the MCP server
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    response_queue = queue.Queue()
    reader_thread = threading.Thread(target=read_responses, args=(process, response_queue))
    reader_thread.daemon = True
    reader_thread.start()
    
    try:
        print("⏳ Waiting for server startup...")
        time.sleep(8)
        
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
        
        # Read init response with timeout
        try:
            init_response_line = response_queue.get(timeout=10)
            print(f"📥 Init response: {init_response_line}")
            init_response = json.loads(init_response_line)
            print(f"✅ Server initialized: {init_response.get('result', {}).get('serverInfo', {}).get('name')}")
        except queue.Empty:
            print("❌ Initialize request timed out")
            return False
        
        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized"
        }
        
        print("📤 Sending initialized notification...")
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()
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
        
        # Read all responses with timeout
        print("📥 Reading responses...")
        responses = []
        timeout_time = time.time() + 30  # 30 second timeout
        
        while time.time() < timeout_time:
            try:
                response_line = response_queue.get(timeout=5)
                print(f"📥 Response: {response_line}")
                responses.append(response_line)
                
                # Check if this is our tool response
                if response_line.startswith('{"jsonrpc":"2.0","id":2'):
                    response = json.loads(response_line)
                    if "result" in response:
                        print("✅ Tool executed successfully")
                        if "content" in response["result"]:
                            content_text = response["result"]["content"][0]["text"]
                            content = json.loads(content_text)
                            print(f"📋 Status: {content.get('status')}")
                        return True
                    elif "error" in response:
                        print(f"❌ Tool returned error: {response['error']}")
                        return False
                        
            except queue.Empty:
                print("⏳ Waiting for more responses...")
                continue
                
        print("❌ Tool response timeout")
        return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        process.terminate()

if __name__ == "__main__":
    success = test_status_with_timeout()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")