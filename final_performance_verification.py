#!/usr/bin/env python3
"""
Final Performance Verification of Enhanced MCP
===============================================
Tests all 9 tools with timeout handling and improved error responses.
"""

import json
import subprocess
import time
import threading
import queue
from typing import Dict, List

class MCPPerformanceTester:
    def __init__(self):
        self.process = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.test_results = {}
        
    def start_server(self):
        """Start the MCP server"""
        print("🚀 Starting Enhanced MCP Server...")
        self.process = subprocess.Popen(
            ["./start_enhanced_fixed.sh"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Start response reader thread
        self.reader_thread = threading.Thread(target=self._read_responses)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        # Wait for startup
        time.sleep(10)
        
    def _read_responses(self):
        """Read responses in separate thread"""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.response_queue.put(line.strip())
        except Exception as e:
            self.response_queue.put(f"ERROR: {e}")
            
    def initialize_mcp(self):
        """Initialize MCP connection"""
        print("📤 Initializing MCP connection...")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "performance_test", "version": "1.0"}
            },
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        # Read response
        try:
            response_line = self.response_queue.get(timeout=15)
            response = json.loads(response_line)
            if response.get("result", {}).get("serverInfo", {}).get("name") == "msfconsole-enhanced":
                print("✅ MCP initialized successfully")
                
                # Send initialized notification
                initialized_notification = {
                    "jsonrpc": "2.0",
                    "method": "notifications/initialized"
                }
                self.process.stdin.write(json.dumps(initialized_notification) + "\n")
                self.process.stdin.flush()
                time.sleep(2)
                return True
            else:
                print("❌ MCP initialization failed")
                return False
        except Exception as e:
            print(f"❌ MCP initialization error: {e}")
            return False
            
    def test_tool(self, tool_name: str, arguments: Dict = None, timeout: int = 30) -> Dict:
        """Test a specific tool"""
        print(f"🔧 Testing {tool_name}...")
        
        # Prepare request
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            },
            "id": hash(tool_name) % 1000  # Unique ID per tool
        }
        
        # Send request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Wait for response
        start_time = time.time()
        timeout_time = start_time + timeout
        
        while time.time() < timeout_time:
            try:
                response_line = self.response_queue.get(timeout=5)
                
                # Skip notifications
                if '"method":"notifications/' in response_line:
                    continue
                    
                # Check if this is our response
                if f'"id":{hash(tool_name) % 1000}' in response_line:
                    response = json.loads(response_line)
                    execution_time = time.time() - start_time
                    
                    if "result" in response:
                        return {
                            "status": "success",
                            "execution_time": execution_time,
                            "has_content": "content" in response["result"],
                            "response_size": len(response_line)
                        }
                    elif "error" in response:
                        return {
                            "status": "error",
                            "execution_time": execution_time,
                            "error": response["error"],
                            "error_message": response["error"].get("message", "Unknown error")
                        }
                        
            except queue.Empty:
                continue
        
        return {
            "status": "timeout",
            "execution_time": timeout,
            "error": "Tool response timeout"
        }
        
    def run_comprehensive_test(self):
        """Run comprehensive test of all tools"""
        print("🔍 Running Comprehensive MCP Performance Test")
        print("=" * 60)
        
        # Test configuration
        tools_to_test = [
            ("get_msf_status", {}),
            ("execute_msf_command", {"command": "version"}),
            ("search_modules", {"query": "ms17_010"}),
            ("manage_workspaces", {"action": "list"}),
            ("database_operations", {"operation": "hosts"}),
            ("session_management", {"action": "list"}),
            ("module_operations", {"action": "info", "module_path": "auxiliary/scanner/portscan/tcp"}),
            ("payload_generation", {"payload_type": "windows/meterpreter/reverse_tcp", "options": {"LHOST": "127.0.0.1", "LPORT": "4444"}}),
            ("resource_script_execution", {"script_commands": ["version", "help"]})
        ]
        
        # Test each tool
        results = {}
        for tool_name, arguments in tools_to_test:
            results[tool_name] = self.test_tool(tool_name, arguments, timeout=45)
            time.sleep(1)  # Brief pause between tests
            
        return results
        
    def generate_report(self, results: Dict):
        """Generate performance report"""
        print("\n" + "=" * 60)
        print("📊 FINAL PERFORMANCE REPORT")
        print("=" * 60)
        
        success_count = 0
        timeout_count = 0
        error_count = 0
        total_execution_time = 0
        
        for tool_name, result in results.items():
            status = result["status"]
            exec_time = result.get("execution_time", 0)
            total_execution_time += exec_time
            
            if status == "success":
                print(f"✅ {tool_name}: SUCCESS ({exec_time:.2f}s)")
                success_count += 1
            elif status == "timeout":
                print(f"⏰ {tool_name}: TIMEOUT ({exec_time:.2f}s)")
                timeout_count += 1
            elif status == "error":
                error_msg = result.get("error_message", "Unknown error")
                print(f"❌ {tool_name}: ERROR - {error_msg} ({exec_time:.2f}s)")
                error_count += 1
                
        print("\n" + "-" * 60)
        print(f"📈 SUMMARY:")
        print(f"   Total Tools: {len(results)}")
        print(f"   ✅ Successful: {success_count} ({success_count/len(results)*100:.1f}%)")
        print(f"   ⏰ Timeouts: {timeout_count} ({timeout_count/len(results)*100:.1f}%)")
        print(f"   ❌ Errors: {error_count} ({error_count/len(results)*100:.1f}%)")
        print(f"   ⏱️  Total Execution Time: {total_execution_time:.2f}s")
        print(f"   ⚡ Average Response Time: {total_execution_time/len(results):.2f}s")
        
        # Determine overall status
        if success_count >= 7:  # 77%+ success rate
            print(f"\n🎉 OVERALL STATUS: EXCELLENT")
        elif success_count >= 5:  # 55%+ success rate
            print(f"\n✅ OVERALL STATUS: GOOD")
        elif success_count >= 3:  # 33%+ success rate
            print(f"\n⚠️  OVERALL STATUS: NEEDS IMPROVEMENT")
        else:
            print(f"\n❌ OVERALL STATUS: POOR")
            
        return results
    
    def cleanup(self):
        """Clean up resources"""
        if self.process:
            self.process.terminate()
            
def main():
    tester = MCPPerformanceTester()
    
    try:
        # Start server and initialize
        tester.start_server()
        if not tester.initialize_mcp():
            print("❌ Failed to initialize MCP - aborting test")
            return 1
            
        # Run comprehensive test
        results = tester.run_comprehensive_test()
        
        # Generate report
        final_results = tester.generate_report(results)
        
        # Save results to file
        with open("final_performance_report.json", "w") as f:
            json.dump(final_results, f, indent=2)
        print(f"\n📄 Detailed results saved to: final_performance_report.json")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit(main())