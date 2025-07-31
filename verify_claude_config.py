#!/usr/bin/env python3

"""
Verify Claude Desktop Configuration
----------------------------------
Check that the enhanced MSF MCP is properly configured for Claude Desktop.
"""

import json
import os
import sys
from pathlib import Path

def check_claude_config():
    """Check Claude Desktop configuration."""
    print("🔍 Verifying Claude Desktop Configuration...")
    print("=" * 50)
    
    # Find Claude config file
    config_paths = [
        Path.home() / ".config" / "claude" / "settings.json",
        Path.home() / ".config" / "claude-desktop" / "claude_desktop_config.json",
        Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    ]
    
    config_file = None
    for path in config_paths:
        if path.exists():
            config_file = path
            break
    
    if not config_file:
        print("❌ Claude Desktop configuration file not found!")
        print("Expected locations:")
        for path in config_paths:
            print(f"   - {path}")
        return False
    
    print(f"✅ Found Claude config: {config_file}")
    
    # Read configuration
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Error reading config file: {e}")
        return False
    
    # Check for MCP servers
    if "mcpServers" not in config:
        print("❌ No mcpServers section found in configuration")
        return False
    
    mcp_servers = config["mcpServers"]
    print(f"✅ Found {len(mcp_servers)} MCP server(s) configured")
    
    # Check for our enhanced MSF MCP
    msf_server_names = ["metasploit-enhanced", "msfconsole-enhanced", "metasploit"]
    msf_server = None
    msf_server_name = None
    
    for name in msf_server_names:
        if name in mcp_servers:
            msf_server = mcp_servers[name]
            msf_server_name = name
            break
    
    if not msf_server:
        print("❌ Enhanced MSF MCP server not found in configuration")
        print("Available servers:")
        for name in mcp_servers.keys():
            print(f"   - {name}")
        return False
    
    print(f"✅ Found MSF MCP server: {msf_server_name}")
    
    # Verify server configuration
    print("\n📋 Server Configuration:")
    print(f"   Command: {msf_server.get('command', 'Not specified')}")
    print(f"   Args: {msf_server.get('args', [])}")
    
    # Check if command file exists
    command = msf_server.get('command')
    if command:
        command_path = Path(command)
        if command_path.exists():
            print(f"   ✅ Command file exists: {command}")
            if os.access(command, os.X_OK):
                print("   ✅ Command file is executable")
            else:
                print("   ⚠️  Command file not executable")
        else:
            print(f"   ❌ Command file not found: {command}")
            return False
    
    # Check project directory
    project_dir = Path("/home/dell/coding/mcp/msfconsole")
    if project_dir.exists():
        print(f"   ✅ Project directory exists: {project_dir}")
        
        # Check key files
        key_files = [
            "msfconsole_mcp_enhanced.py",
            "msf_rpc_manager.py", 
            "msf_dual_mode.py",
            "msf_security.py",
            "launch_mcp_for_claude.sh",
            "venv_enhanced/bin/python"
        ]
        
        missing_files = []
        for file in key_files:
            file_path = project_dir / file
            if file_path.exists():
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file}")
                missing_files.append(file)
        
        if missing_files:
            print(f"\n⚠️  Missing {len(missing_files)} required files")
            return False
    else:
        print(f"   ❌ Project directory not found: {project_dir}")
        return False
    
    print("\n🎉 Configuration verification completed successfully!")
    print("\n📝 Next steps:")
    print("1. Restart Claude Desktop application")
    print("2. Look for 'metasploit-enhanced' in the MCP servers list")
    print("3. Test with a command like: 'Get MSF status'")
    
    return True

def main():
    """Main function."""
    try:
        success = check_claude_config()
        if success:
            print("\n✅ All checks passed! Enhanced MSF MCP should be available in Claude Desktop.")
            sys.exit(0)
        else:
            print("\n❌ Configuration issues found. Please fix the issues above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error during verification: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()