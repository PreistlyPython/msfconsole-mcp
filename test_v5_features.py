#!/usr/bin/env python3
"""
Test script for MSF Console MCP v5.0 features
Tests plugin system, core commands, and session management
"""

import asyncio
import json
import sys
from datetime import datetime

# Add path for imports
sys.path.insert(0, '.')

from mcp_server_stable import MSFConsoleMCPServer


async def test_v5_features():
    """Test all v5.0 features"""
    server = MSFConsoleMCPServer()
    
    print("\n🚀 MSF Console MCP v5.0 Feature Test Suite")
    print("=" * 60)
    
    # Initialize server
    print("\n📦 Initializing MCP Server v5.0...")
    try:
        await server.initialize()
        print("✅ Server initialized successfully")
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Test results
    results = {
        "total_tests": 0,
        "passed": 0,
        "failed": 0,
        "features_tested": []
    }
    
    # ========== TEST PLUGIN SYSTEM ==========
    print("\n\n🔌 Testing Enhanced Plugin System")
    print("-" * 40)
    
    # Test 1: List plugins
    print("\n1️⃣ Testing plugin listing...")
    try:
        result = await server.handle_tool_call("msf_enhanced_plugin_manager", {
            "action": "list"
        })
        data = json.loads(result["content"][0]["text"])
        plugin_count = len(data.get("plugins", []))
        print(f"✅ Found {plugin_count} plugins available")
        results["passed"] += 1
        results["features_tested"].append("plugin_listing")
    except Exception as e:
        print(f"❌ Plugin listing failed: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 2: Load plugin
    print("\n2️⃣ Testing plugin loading (auto_add_route)...")
    try:
        result = await server.handle_tool_call("msf_enhanced_plugin_manager", {
            "action": "load",
            "plugin_name": "auto_add_route"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Plugin loaded: {data.get('data', {}).get('plugin')}")
            results["passed"] += 1
            results["features_tested"].append("plugin_loading")
        else:
            print(f"❌ Plugin load failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Plugin loading error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 3: Execute plugin command
    print("\n3️⃣ Testing plugin command execution...")
    try:
        result = await server.handle_tool_call("msf_enhanced_plugin_manager", {
            "action": "execute",
            "plugin_name": "auto_add_route",
            "command": "status"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Plugin command executed successfully")
            print(f"   Status: {data.get('data', {})}")
            results["passed"] += 1
            results["features_tested"].append("plugin_commands")
        else:
            print(f"❌ Plugin command failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Plugin command error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # ========== TEST CORE COMMANDS ==========
    print("\n\n⚡ Testing Core Commands")
    print("-" * 40)
    
    # Test 4: Network routing (route command)
    print("\n4️⃣ Testing route manager...")
    try:
        result = await server.handle_tool_call("msf_route_manager", {
            "action": "list"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Route manager working - {len(data.get('data', {}).get('routes', []))} routes")
            results["passed"] += 1
            results["features_tested"].append("route_manager")
        else:
            print(f"❌ Route manager failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Route manager error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 5: Output filtering (grep command)
    print("\n5️⃣ Testing output filter (grep)...")
    try:
        result = await server.handle_tool_call("msf_output_filter", {
            "pattern": "version",
            "command": "version"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Output filter working - {data.get('data', {}).get('matches', 0)} matches")
            results["passed"] += 1
            results["features_tested"].append("output_filter")
        else:
            print(f"❌ Output filter failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Output filter error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 6: Console logger (spool command)
    print("\n6️⃣ Testing console logger...")
    try:
        result = await server.handle_tool_call("msf_console_logger", {
            "action": "status"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Console logger status: {data.get('data', {})}")
            results["passed"] += 1
            results["features_tested"].append("console_logger")
        else:
            print(f"❌ Console logger failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Console logger error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 7: Config manager (save command)
    print("\n7️⃣ Testing config manager...")
    try:
        result = await server.handle_tool_call("msf_config_manager", {
            "action": "list"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Config manager working - {len(data.get('data', {}).get('configurations', []))} configs")
            results["passed"] += 1
            results["features_tested"].append("config_manager")
        else:
            print(f"❌ Config manager failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Config manager error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # ========== TEST SESSION MANAGEMENT ==========
    print("\n\n🎯 Testing Advanced Session Management")
    print("-" * 40)
    
    # Test 8: Session clustering
    print("\n8️⃣ Testing session clustering...")
    try:
        result = await server.handle_tool_call("msf_session_clustering", {
            "action": "create",
            "group_name": "test_group"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Session clustering working - created group: {data.get('data', {}).get('group')}")
            results["passed"] += 1
            results["features_tested"].append("session_clustering")
        else:
            print(f"❌ Session clustering failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Session clustering error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # Test 9: Session persistence
    print("\n9️⃣ Testing session persistence...")
    try:
        result = await server.handle_tool_call("msf_session_persistence", {
            "action": "list"
        })
        data = json.loads(result["content"][0]["text"])
        if data.get("success"):
            print(f"✅ Session persistence working - {len(data.get('data', {}).get('persistence_handlers', []))} handlers")
            results["passed"] += 1
            results["features_tested"].append("session_persistence")
        else:
            print(f"❌ Session persistence failed: {data.get('error')}")
            results["failed"] += 1
    except Exception as e:
        print(f"❌ Session persistence error: {e}")
        results["failed"] += 1
    results["total_tests"] += 1
    
    # ========== SUMMARY ==========
    print("\n\n📊 Test Results Summary")
    print("=" * 60)
    print(f"Total Tests: {results['total_tests']}")
    print(f"✅ Passed: {results['passed']}")
    print(f"❌ Failed: {results['failed']}")
    print(f"Success Rate: {(results['passed'] / results['total_tests'] * 100):.1f}%")
    print(f"\nFeatures Tested: {', '.join(results['features_tested'])}")
    
    # Check feature coverage
    expected_features = [
        "plugin_listing", "plugin_loading", "plugin_commands",
        "route_manager", "output_filter", "console_logger",
        "config_manager", "session_clustering", "session_persistence"
    ]
    missing_features = set(expected_features) - set(results["features_tested"])
    if missing_features:
        print(f"\n⚠️  Missing features: {', '.join(missing_features)}")
    else:
        print(f"\n✅ All expected v5.0 features tested!")
    
    # Cleanup
    await server.cleanup()
    
    return results


if __name__ == "__main__":
    print("MSF Console MCP v5.0 Feature Test")
    print("Testing plugin system, core commands, and session management...")
    
    try:
        results = asyncio.run(test_v5_features())
        
        # Exit with appropriate code
        if results["failed"] == 0:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print(f"\n⚠️  {results['failed']} tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nTest suite error: {e}")
        sys.exit(1)