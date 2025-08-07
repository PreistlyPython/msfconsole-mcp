#!/usr/bin/env python3

"""
Update Claude Code Configuration with MSFConsole MCP
---------------------------------------------------
Safely update the .claude.json file to add our production-ready MSFConsole MCP server.
"""

import json
import os
import shutil
from pathlib import Path

def backup_config(config_path):
    """Create a backup of the current config."""
    backup_path = f"{config_path}.backup.{int(__import__('time').time())}"
    shutil.copy2(config_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def update_claude_config():
    """Update Claude Code configuration with MSFConsole MCP."""
    config_path = "/home/dell/.claude.json"
    
    # Backup first
    backup_path = backup_config(config_path)
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        print(f"✅ Loaded configuration file (size: {os.path.getsize(config_path):,} bytes)")
        
        # MSFConsole MCP server configuration
        msfconsole_mcp_config = {
            "msfconsole-stable": {
                "type": "stdio",
                "command": "python3",
                "args": ["/home/dell/coding/mcp/msfconsole/mcp_server_stable.py"],
                "env": {
                    "PYTHONPATH": "/home/dell/coding/mcp/msfconsole",
                    "MSF_DATABASE_CONFIG": "/dev/null",
                    "RUBY_GC_HEAP_INIT_SLOTS": "100000",
                    "LANG": "en_US.UTF-8"
                }
            }
        }
        
        # Update projects that need MSFConsole MCP
        projects_to_update = [
            "/home/dell/coding/mcp/msfconsole",
            "/home/dell/coding/mcp/wireshark-mcp"
        ]
        
        updated_projects = 0
        
        for project_path in projects_to_update:
            if project_path in config["projects"]:
                # Initialize mcpServers if it doesn't exist
                if "mcpServers" not in config["projects"][project_path]:
                    config["projects"][project_path]["mcpServers"] = {}
                
                # Add/update the MSFConsole MCP configuration
                config["projects"][project_path]["mcpServers"].update(msfconsole_mcp_config)
                updated_projects += 1
                print(f"✅ Updated {project_path}")
            else:
                print(f"⚠️ Project not found: {project_path}")
        
        if updated_projects > 0:
            # Save updated configuration
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Successfully updated {updated_projects} project configurations")
            print("\n🎯 MSFConsole MCP Configuration Added:")
            print(json.dumps(msfconsole_mcp_config, indent=2))
            
            print("\n📋 Next Steps:")
            print("1. Restart Claude Code for changes to take effect")
            print("2. Test MSFConsole MCP with: 'Use msf_get_status to check server health'")
            print("3. Verify all 8 MSF tools are available in Claude Code")
            
            return True
        else:
            print("❌ No projects were updated")
            return False
            
    except Exception as e:
        print(f"❌ Error updating configuration: {e}")
        # Restore backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, config_path)
            print(f"✅ Restored backup from: {backup_path}")
        return False

def verify_mcp_server():
    """Verify our MCP server is working before configuration."""
    server_path = "/home/dell/coding/mcp/msfconsole/mcp_server_stable.py"
    
    if not os.path.exists(server_path):
        print(f"❌ MCP server not found: {server_path}")
        return False
    
    if not os.access(server_path, os.X_OK):
        print(f"⚠️ Making MCP server executable: {server_path}")
        os.chmod(server_path, 0o755)
    
    print(f"✅ MCP server verified: {server_path}")
    return True

def main():
    """Main configuration update process."""
    print("🚀 Claude Code MSFConsole MCP Configuration Update")
    print("=" * 60)
    
    # Verify MCP server
    if not verify_mcp_server():
        print("❌ MCP server verification failed")
        return False
    
    # Update configuration
    if update_claude_config():
        print("\n🎉 Configuration update completed successfully!")
        print("\n🔄 Please restart Claude Code to activate the MSFConsole MCP server.")
        return True
    else:
        print("\n❌ Configuration update failed")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)