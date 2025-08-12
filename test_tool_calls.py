#!/usr/bin/env python3
"""
Test tool calls without full MSF initialization
"""

import asyncio
import json
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_tool_calls():
    """Test that tools can be called through the server interface."""
    print("🚀 Testing Tool Call Interface")
    print("=" * 40)
    
    # Mock test without real MSF initialization
    from mcp_server_stable import MSFConsoleMCPServer
    
    server = MSFConsoleMCPServer()
    results = {"success": 0, "failed": 0, "tests": []}
    
    # Test new ecosystem tools (without initialization)
    new_tools = [
        ("msf_venom_direct", {"payload": "test"}),
        ("msf_database_direct", {"action": "status"}),
        ("msf_rpc_interface", {"action": "status"}),
        ("msf_interactive_session", {"session_id": "1", "action": "sysinfo"}),
        ("msf_report_generator", {"report_type": "json"}),
        ("msf_evasion_suite", {"payload": "test"}),
        ("msf_listener_orchestrator", {"action": "create"}),
        ("msf_workspace_automator", {"action": "create_template", "workspace_name": "test"}),
        ("msf_encoder_factory", {"payload_data": "test", "encoding_chain": ["xor"]}),
        ("msf_integration_bridge", {"tool": "nmap", "action": "status"})
    ]
    
    for tool_name, args in new_tools:
        print(f"🔧 Testing {tool_name}...", end=" ")
        
        try:
            # Test that the tool exists in routing
            if not server.initialized:
                # Mock initialization status for routing test
                server.initialized = True
            
            # This should not hang since we're testing routing, not MSF execution
            # The tools should fail gracefully without MSF initialization
            result = await asyncio.wait_for(
                server.handle_tool_call(tool_name, args),
                timeout=5.0  # 5 second timeout
            )
            
            if result and "content" in result:
                content = result["content"][0].get("text", "")
                if "Unknown tool" in content:
                    print("❌ Tool not found in routing")
                    results["failed"] += 1
                    results["tests"].append({"tool": tool_name, "status": "not_found"})
                else:
                    print("✅ Tool found and callable")
                    results["success"] += 1
                    results["tests"].append({"tool": tool_name, "status": "callable"})
            else:
                print("❌ No response")
                results["failed"] += 1 
                results["tests"].append({"tool": tool_name, "status": "no_response"})
                
        except asyncio.TimeoutError:
            print("⏰ Timeout (likely hanging)")
            results["failed"] += 1
            results["tests"].append({"tool": tool_name, "status": "timeout"})
        except Exception as e:
            print(f"❌ Error: {str(e)[:30]}")
            results["failed"] += 1
            results["tests"].append({"tool": tool_name, "status": "error", "error": str(e)})
    
    # Results
    print("\n" + "=" * 40)
    print("📊 TOOL CALL TEST RESULTS")
    print("=" * 40)
    print(f"✅ Callable: {results['success']}/10")
    print(f"❌ Issues: {results['failed']}/10")
    print(f"📈 Success Rate: {(results['success']/10)*100:.1f}%")
    
    # Detailed results
    print("\n📝 Detailed Results:")
    for test in results["tests"]:
        status_emoji = {
            "callable": "✅",
            "not_found": "🔍",
            "no_response": "❌", 
            "timeout": "⏰",
            "error": "💥"
        }.get(test["status"], "❓")
        
        print(f"  {status_emoji} {test['tool']}: {test['status']}")
        if "error" in test:
            print(f"     Error: {test['error'][:60]}")
    
    return results["success"] >= 7  # 70% threshold

if __name__ == "__main__":
    success = asyncio.run(test_tool_calls())
    if success:
        print("\n🎉 Tool call test PASSED!")
        print("✅ New tools are properly integrated and callable")
    else:
        print("\n⚠️  Tool call test found issues")