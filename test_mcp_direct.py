#!/usr/bin/env python3
"""
Direct test of MSF Console MCP tools via Claude Code's MCP interface
Tests basic connectivity and tool availability
"""

import asyncio
import json
import sys

def test_mcp_tools():
    """Test MSF Console MCP tools availability"""
    
    print("🚀 Testing MSF Console MCP Tool Connectivity...")
    print("=" * 60)
    
    # Test different possible naming conventions
    tool_patterns = [
        "msf_execute_command",
        "mcp__msf_execute_command", 
        "mcp__msfconsole__msf_execute_command",
        "mcp__msfconsole-fixed__msf_execute_command",
        "msfconsole_execute_command",
        "execute_command"
    ]
    
    print(f"Testing {len(tool_patterns)} possible tool naming patterns:")
    for i, pattern in enumerate(tool_patterns, 1):
        print(f"{i}. {pattern}")
    
    print("\n⚠️  NOTE: This script shows possible naming patterns.")
    print("💡 To test actual tools, call them directly via Claude Code's MCP interface.")
    print("\n🎯 Based on MCP configuration (.mcp.json), tools should use pattern:")
    print("   'msf_execute_command' (no prefix)")
    
    print("\n📋 Basic test commands to try:")
    test_commands = [
        {"tool": "msf_execute_command", "args": {"command": "version"}},
        {"tool": "msf_get_status", "args": {}},
        {"tool": "msf_search_modules", "args": {"query": "unifi", "limit": 5}},
        {"tool": "msf_create_workspace", "args": {"name": "test_workspace"}},
        {"tool": "msf_list_workspaces", "args": {}}
    ]
    
    for i, cmd in enumerate(test_commands, 1):
        print(f"\n{i}. Tool: {cmd['tool']}")
        print(f"   Args: {json.dumps(cmd['args'], indent=2)}")
    
    print("\n" + "=" * 60)
    print("✅ Use these patterns to test MSF Console MCP tools directly via Claude Code")

if __name__ == "__main__":
    test_mcp_tools()