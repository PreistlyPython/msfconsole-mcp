#!/usr/bin/env python3
"""Final verification of the enhanced MCP implementation"""

import json
import subprocess
import time

def test_mcp_server():
    """Test the MCP server functionality"""
    print("🔍 Final Verification of Enhanced MCP Server")
    print("=" * 60)
    
    # Check configuration
    config_path = "/home/dell/.config/Claude/claude_desktop_config.json"
    print(f"📋 Checking Claude Desktop configuration...")
    with open(config_path) as f:
        config = json.load(f)
    
    if "msfconsole-enhanced" in config.get("mcpServers", {}):
        print("✅ msfconsole-enhanced found in Claude config")
        command = config["mcpServers"]["msfconsole-enhanced"]["command"]
        print(f"   Command: {command}")
    else:
        print("❌ msfconsole-enhanced not found in config")
        return False
    
    # Test the server startup
    print(f"\n🚀 Testing MCP server startup...")
    process = subprocess.Popen(
        ["./start_enhanced_fixed.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        time.sleep(3)  # Allow startup
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "verification", "version": "1.0"}
            },
            "id": 1
        }
        
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        response = json.loads(response_line)
        
        if response.get("result", {}).get("serverInfo", {}).get("name") == "msfconsole-enhanced":
            print("✅ Server responds correctly to initialize")
            
            # Test tools list
            tools_request = {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 2
            }
            
            process.stdin.write(json.dumps(tools_request) + "\n")
            process.stdin.flush()
            
            tools_response = json.loads(process.stdout.readline())
            tools = tools_response.get("result", {}).get("tools", [])
            
            print(f"✅ Server has {len(tools)} tools available:")
            for tool in tools[:5]:  # Show first 5 tools
                print(f"   - {tool['name']}")
            if len(tools) > 5:
                print(f"   ... and {len(tools) - 5} more tools")
                
            return True
        else:
            print("❌ Server response incorrect")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        process.terminate()

def main():
    success = test_mcp_server()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\nThe enhanced Metasploit MCP server is ready to use.")
        print("You should now see 'msfconsole-enhanced' in Claude Desktop with 9 tools.")
        print("\nNext steps:")
        print("1. Restart Claude Desktop if it's running")
        print("2. Look for 'msfconsole-enhanced' in the MCP tools list")
        print("3. Try using the tools like get_msf_status or search_modules")
    else:
        print("❌ Some tests failed. Please check the issues above.")
        print("Make sure Metasploit is properly installed and configured.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())