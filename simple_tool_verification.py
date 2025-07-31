#!/usr/bin/env python3
"""Simple verification of MCP tools functionality"""

import subprocess
import time
import json
import select

def test_mcp_tools():
    print("🔍 Simple MCP Tools Verification")
    print("=" * 50)
    
    # Start server
    print("🚀 Starting MCP server...")
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Wait for startup
        time.sleep(15)
        
        # Initialize
        print("📤 Initializing connection...")
        init_request = '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}},"id":1}\n'
        process.stdin.write(init_request)
        process.stdin.flush()
        
        # Read init response
        if select.select([process.stdout], [], [], 10):
            response = process.stdout.readline()
            init_data = json.loads(response)
            if "result" in init_data:
                print("✅ MCP initialized successfully")
            else:
                print("❌ MCP initialization failed")
                return False
        else:
            print("❌ No init response")
            return False
        
        # Send initialized notification
        init_notify = '{"jsonrpc":"2.0","method":"notifications/initialized"}\n'
        process.stdin.write(init_notify)
        process.stdin.flush()
        time.sleep(2)
        
        # Test tools
        tools_to_test = [
            ("get_msf_status", {}),
            ("execute_msf_command", {"command": "version"}),
            ("search_modules", {"query": "ms17_010"}),
        ]
        
        results = {}
        
        for i, (tool_name, args) in enumerate(tools_to_test, 2):
            print(f"🔧 Testing {tool_name}...")
            
            # Create request
            request = {
                "jsonrpc": "2.0",
                "method": "tools/call", 
                "params": {"name": tool_name, "arguments": args},
                "id": i
            }
            
            # Send request
            process.stdin.write(json.dumps(request) + "\n")
            process.stdin.flush()
            
            # Read response with timeout
            timeout = time.time() + 30
            while time.time() < timeout:
                if select.select([process.stdout], [], [], 5):
                    line = process.stdout.readline().strip()
                    if not line:
                        continue
                        
                    # Skip notifications
                    if '"method":"notifications/' in line:
                        continue
                    
                    try:
                        response_data = json.loads(line)
                        if response_data.get("id") == i:
                            if "result" in response_data:
                                print(f"✅ {tool_name}: SUCCESS")
                                results[tool_name] = "success"
                            elif "error" in response_data:
                                error_msg = response_data["error"].get("message", "Unknown error")
                                print(f"⚠️  {tool_name}: ERROR - {error_msg}")
                                results[tool_name] = f"error: {error_msg}"
                            break
                    except json.JSONDecodeError:
                        continue
                else:
                    continue
            else:
                print(f"⏰ {tool_name}: TIMEOUT")
                results[tool_name] = "timeout"
            
            time.sleep(1)  # Brief pause between tests
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        process.terminate()

def main():
    results = test_mcp_tools()
    
    if results:
        print("\n" + "=" * 50)
        print("📊 VERIFICATION RESULTS")
        print("=" * 50)
        
        success_count = sum(1 for result in results.values() if result == "success")
        total_count = len(results)
        
        for tool_name, result in results.items():
            if result == "success":
                print(f"✅ {tool_name}")
            elif result == "timeout":
                print(f"⏰ {tool_name}")
            else:
                print(f"❌ {tool_name}: {result}")
        
        print(f"\nSUCCESS RATE: {success_count}/{total_count} ({success_count/total_count*100:.1f}%)")
        
        if success_count == total_count:
            print("🎉 ALL TOOLS WORKING!")
        elif success_count >= total_count * 0.7:
            print("✅ MOST TOOLS WORKING!")
        else:
            print("⚠️  SOME TOOLS NEED ATTENTION")
            
        return 0 if success_count >= total_count * 0.7 else 1
    else:
        print("❌ VERIFICATION FAILED")
        return 1

if __name__ == "__main__":
    exit(main())