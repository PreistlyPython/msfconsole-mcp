#!/usr/bin/env python3
"""Test enhanced MCP fixes"""

import asyncio
import json
import subprocess

async def test_search_command():
    """Test the search command with the enhanced MCP"""
    
    # Launch the MCP server
    proc = subprocess.Popen(
        ["./launch_mcp_for_claude.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
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
        
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        response = json.loads(proc.stdout.readline())
        print(f"✅ Initialize: {response['result']['serverInfo']['name']}")
        
        # Test search command
        search_request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "search_modules",
                "arguments": {
                    "query": "ms17_010",
                    "module_type": "exploit"
                }
            },
            "id": 2
        }
        
        print("🔍 Testing search_modules...")
        proc.stdin.write(json.dumps(search_request) + "\n")
        proc.stdin.flush()
        
        # Wait for response with timeout
        try:
            response_line = await asyncio.wait_for(
                asyncio.create_task(read_line_async(proc.stdout)), 
                timeout=360  # 6 minutes
            )
            response = json.loads(response_line)
            
            if "result" in response:
                result = json.loads(response["result"]["content"][0]["text"])
                if result["success"]:
                    print(f"✅ Search successful: Found {result['results_count']} modules")
                    for module in result.get("modules", [])[:3]:  # Show first 3
                        print(f"   - {module.get('name', 'Unknown')}")
                else:
                    print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            else:
                print(f"❌ Unexpected response: {response}")
                
        except asyncio.TimeoutError:
            print("❌ Search timed out after 6 minutes")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
    finally:
        proc.terminate()

async def read_line_async(stdout):
    """Async wrapper for reading a line"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, stdout.readline)

async def main():
    print("🧪 Testing Enhanced MCP Fixes")
    print("=" * 50)
    await test_search_command()

if __name__ == "__main__":
    asyncio.run(main())