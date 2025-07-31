#!/usr/bin/env python3
"""Verify enhanced MCP setup and configuration"""

import os
import json
import subprocess
import sys

def check_claude_config():
    """Check Claude Desktop configuration"""
    config_path = os.path.expanduser("~/.config/Claude/claude_desktop_config.json")
    
    if not os.path.exists(config_path):
        print("❌ Claude Desktop config not found")
        return False
        
    with open(config_path, 'r') as f:
        config = json.load(f)
        
    mcps = config.get("mcpServers", {})
    
    if "msfconsole-enhanced" in mcps:
        print("✅ msfconsole-enhanced found in Claude config")
        print(f"   Command: {mcps['msfconsole-enhanced']['command']}")
        return True
    else:
        print("❌ msfconsole-enhanced not found in Claude config")
        print(f"   Found MCPs: {list(mcps.keys())}")
        return False

def test_launch_script():
    """Test the launch script"""
    launch_script = "./launch_mcp_for_claude.sh"
    
    if not os.path.exists(launch_script):
        print("❌ Launch script not found")
        return False
        
    if not os.access(launch_script, os.X_OK):
        print("❌ Launch script not executable")
        return False
        
    print("✅ Launch script exists and is executable")
    return True

def test_virtual_env():
    """Test virtual environment setup"""
    venv_python = "./venv_enhanced/bin/python"
    
    if not os.path.exists(venv_python):
        print("❌ Virtual environment Python not found")
        return False
        
    # Test MCP import
    result = subprocess.run(
        [venv_python, "-c", "from mcp.server.fastmcp import FastMCP; print('OK')"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip() == "OK":
        print("✅ Virtual environment can import MCP")
        return True
    else:
        print("❌ Virtual environment cannot import MCP")
        print(f"   Error: {result.stderr}")
        return False

def test_enhanced_modules():
    """Test enhanced module imports"""
    modules = ["msf_rpc_manager", "msf_dual_mode", "msf_security", "msf_config"]
    
    for module in modules:
        if not os.path.exists(f"{module}.py"):
            print(f"❌ Module {module}.py not found")
            return False
            
    print("✅ All enhanced modules found")
    return True

def test_mcp_server():
    """Test MCP server startup"""
    print("\nTesting MCP server startup...")
    
    # Test basic protocol
    proc = subprocess.Popen(
        ["./launch_mcp_for_claude.sh"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialize
        init_req = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1.0"}
            },
            "id": 1
        }
        
        proc.stdin.write(json.dumps(init_req) + "\n")
        proc.stdin.flush()
        
        # Read response
        response_line = proc.stdout.readline()
        response = json.loads(response_line)
        
        if response.get("result", {}).get("serverInfo", {}).get("name") == "msfconsole-enhanced":
            print("✅ MCP server responds correctly")
            print(f"   Version: {response['result']['serverInfo']['version']}")
            return True
        else:
            print("❌ MCP server response incorrect")
            print(f"   Response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ MCP server test failed: {e}")
        stderr = proc.stderr.read()
        if stderr:
            print(f"   Stderr: {stderr}")
        return False
    finally:
        proc.terminate()

def main():
    print("🔍 Verifying Enhanced MCP Setup")
    print("=" * 50)
    
    checks = [
        ("Claude Desktop Configuration", check_claude_config),
        ("Launch Script", test_launch_script),
        ("Virtual Environment", test_virtual_env),
        ("Enhanced Modules", test_enhanced_modules),
        ("MCP Server Protocol", test_mcp_server)
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        print(f"\nChecking {name}...")
        if not check_func():
            all_passed = False
            
    print("\n" + "=" * 50)
    
    if all_passed:
        print("✅ All checks passed! Enhanced MCP is ready.")
        print("\nNext steps:")
        print("1. Restart Claude Desktop")
        print("2. Look for 'msfconsole-enhanced' in the MCP tools")
        print("3. The enhanced MCP should show 9 tools")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())