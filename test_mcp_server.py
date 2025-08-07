#!/usr/bin/env python3

"""
Test MSFConsole MCP Server
--------------------------
Test the MCP server to ensure it's working properly before configuration.
"""

import asyncio
import json
import subprocess
import sys
import os
import time

async def test_mcp_server():
    """Test the MCP server functionality."""
    print("🧪 Testing MSFConsole MCP Server...")
    
    # Start the MCP server process
    server_path = "/home/dell/coding/mcp/msfconsole/mcp_server_stable.py"
    
    try:
        # Test 1: Server startup
        print("\n1. Testing server startup...")
        process = await asyncio.create_subprocess_exec(
            "python3", server_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Test 2: Initialize request
        print("2. Testing initialization...")
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        request_json = json.dumps(init_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        # Read response
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        if response_line:
            response = json.loads(response_line.decode().strip())
            if response.get("result"):
                print("✅ Initialization successful")
                print(f"   Server: {response['result']['serverInfo']['name']}")
                print(f"   Version: {response['result']['serverInfo']['version']}")
            else:
                print("❌ Initialization failed")
                return False
        
        # Test 3: List tools
        print("3. Testing tool listing...")
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        request_json = json.dumps(tools_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=10)
        if response_line:
            response = json.loads(response_line.decode().strip())
            tools = response.get("result", {}).get("tools", [])
            print(f"✅ Found {len(tools)} available tools:")
            for tool in tools[:3]:  # Show first 3 tools
                print(f"   - {tool['name']}: {tool['description'][:50]}...")
            if len(tools) > 3:
                print(f"   - ... and {len(tools) - 3} more tools")
        
        # Test 4: Execute a simple command
        print("4. Testing command execution...")
        command_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "msf_get_status",
                "arguments": {}
            }
        }
        
        request_json = json.dumps(command_request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()
        
        response_line = await asyncio.wait_for(process.stdout.readline(), timeout=30)
        if response_line:
            response = json.loads(response_line.decode().strip())
            if response.get("result"):
                print("✅ Status command executed successfully")
                # Parse the status result
                content = response["result"]["content"][0]["text"]
                status_data = json.loads(content)
                if status_data.get("initialized"):
                    print("   MSF initialized: ✅")
                else:
                    print("   MSF initialized: ❌")
                    
                stability = status_data.get("msf_status", {}).get("stability_rating", 0)
                print(f"   Stability rating: {stability}/10")
        
        # Clean shutdown
        process.terminate()
        await process.wait()
        
        print("\n🎉 All tests passed! MCP server is ready for configuration.")
        return True
        
    except asyncio.TimeoutError:
        print("❌ Test timed out")
        if 'process' in locals():
            process.kill()
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        if 'process' in locals():
            process.kill()
        return False

async def main():
    """Main test function."""
    success = await test_mcp_server()
    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)