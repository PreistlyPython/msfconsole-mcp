#!/usr/bin/env python3
"""
Comprehensive MSF MCP Tools Test Suite
=====================================
Thorough testing of all 9 MSF MCP tools with detailed performance analysis.
"""

import subprocess
import time
import json
import threading
import queue
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ToolTestResult:
    tool_name: str
    success: bool
    execution_time: float
    response_size: int
    has_structured_data: bool
    parsing_quality: str
    error_message: str = ""
    sample_data: Any = None

class ComprehensiveMSFTester:
    def __init__(self):
        self.process = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.test_results = {}
        self.start_time = time.time()
        
    def start_mcp_server(self):
        """Start the enhanced MSF MCP server"""
        print("🚀 Starting Enhanced MSF MCP Server for Comprehensive Testing")
        print("=" * 70)
        
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
        
        # Wait for server initialization
        print("⏳ Waiting for server initialization (15 seconds)...")
        time.sleep(15)
        
    def _read_responses(self):
        """Read MCP responses in separate thread"""
        try:
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                self.response_queue.put(line.strip())
        except Exception as e:
            self.response_queue.put(f"READER_ERROR: {e}")
            
    def initialize_mcp_connection(self):
        """Initialize MCP protocol connection"""
        print("📡 Initializing MCP Connection...")
        
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "comprehensive_tester", "version": "1.0"}
            },
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        # Read initialization response
        try:
            response_line = self.response_queue.get(timeout=20)
            response = json.loads(response_line)
            server_name = response.get("result", {}).get("serverInfo", {}).get("name")
            
            if server_name == "msfconsole-enhanced":
                print("✅ MCP Connection Initialized Successfully")
                
                # Send initialized notification
                init_notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                self.process.stdin.write(json.dumps(init_notify) + "\n")
                self.process.stdin.flush()
                time.sleep(3)
                return True
            else:
                print("❌ MCP Initialization Failed - Invalid Server Response")
                return False
                
        except Exception as e:
            print(f"❌ MCP Initialization Error: {e}")
            return False
    
    def test_individual_tool(self, tool_name: str, arguments: Dict, timeout: int = 45) -> ToolTestResult:
        """Test a single MCP tool comprehensively"""
        print(f"\n🔧 Testing Tool: {tool_name}")
        print(f"   Arguments: {arguments}")
        print(f"   Timeout: {timeout}s")
        
        request_id = hash(f"{tool_name}_{time.time()}") % 10000
        start_time = time.time()
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            },
            "id": request_id
        }
        
        # Send tool request
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        # Wait for response
        timeout_time = start_time + timeout
        notifications_received = 0
        
        while time.time() < timeout_time:
            try:
                response_line = self.response_queue.get(timeout=5)
                
                # Count notifications (shows tool is active)
                if '"method":"notifications/' in response_line:
                    notifications_received += 1
                    continue
                    
                # Check for our tool response
                if f'"id":{request_id}' in response_line:
                    execution_time = time.time() - start_time
                    
                    try:
                        response = json.loads(response_line)
                        
                        if "result" in response:
                            # Successful tool execution
                            content = response["result"].get("content", [])
                            response_text = content[0]["text"] if content else str(response["result"])
                            
                            # Parse response data
                            try:
                                response_data = json.loads(response_text)
                                has_structured = isinstance(response_data, dict)
                                
                                # Analyze response quality
                                parsing_quality = self._analyze_response_quality(response_data)
                                
                                return ToolTestResult(
                                    tool_name=tool_name,
                                    success=True,
                                    execution_time=execution_time,
                                    response_size=len(response_text),
                                    has_structured_data=has_structured,
                                    parsing_quality=parsing_quality,
                                    sample_data=self._extract_sample_data(response_data)
                                )
                                
                            except json.JSONDecodeError:
                                # Raw text response
                                return ToolTestResult(
                                    tool_name=tool_name,
                                    success=True,
                                    execution_time=execution_time,
                                    response_size=len(response_text),
                                    has_structured_data=False,
                                    parsing_quality="raw_text",
                                    sample_data=response_text[:200] + "..." if len(response_text) > 200 else response_text
                                )
                        
                        elif "error" in response:
                            # Tool error
                            error = response["error"]
                            execution_time = time.time() - start_time
                            
                            return ToolTestResult(
                                tool_name=tool_name,
                                success=False,
                                execution_time=execution_time,
                                response_size=len(str(error)),
                                has_structured_data=True,
                                parsing_quality="error_response",
                                error_message=error.get("message", str(error))
                            )
                            
                    except json.JSONDecodeError as e:
                        return ToolTestResult(
                            tool_name=tool_name,
                            success=False,
                            execution_time=time.time() - start_time,
                            response_size=len(response_line),
                            has_structured_data=False,
                            parsing_quality="json_parse_error",
                            error_message=f"Invalid JSON response: {str(e)}"
                        )
                        
            except queue.Empty:
                continue
        
        # Timeout
        return ToolTestResult(
            tool_name=tool_name,
            success=False,
            execution_time=timeout,
            response_size=0,
            has_structured_data=False,
            parsing_quality="timeout",
            error_message=f"Tool response timeout after {timeout}s. Notifications received: {notifications_received}"
        )
    
    def _analyze_response_quality(self, data: Dict) -> str:
        """Analyze the quality of structured response data"""
        if not isinstance(data, dict):
            return "non_dict_response"
            
        # Check for success indicators
        if data.get("success") is True:
            # Check for structured data
            if "parsed_output" in data:
                return "excellent_parsed"
            elif any(key in data for key in ["modules", "workspaces", "hosts", "sessions"]):
                return "good_structured"
            elif "output" in data and len(str(data["output"])) > 50:
                return "basic_functional" 
            else:
                return "minimal_data"
        elif data.get("success") is False:
            if "timeout" in str(data.get("error", "")).lower():
                return "timeout_error"
            else:
                return "execution_error"
        else:
            return "unknown_format"
    
    def _extract_sample_data(self, data: Dict) -> Any:
        """Extract a sample of interesting data for display"""
        if isinstance(data, dict):
            if "parsed_output" in data:
                parsed = data["parsed_output"]
                if isinstance(parsed.get("data"), list) and parsed["data"]:
                    return parsed["data"][0]  # First item
                else:
                    return parsed.get("data")
            elif "modules" in data and isinstance(data["modules"], list) and data["modules"]:
                return data["modules"][0]
            elif "workspaces" in data and isinstance(data["workspaces"], list) and data["workspaces"]:
                return data["workspaces"][0]
            elif "output" in data:
                output_str = str(data["output"])
                return output_str[:200] + "..." if len(output_str) > 200 else output_str
        
        return str(data)[:200] + "..." if len(str(data)) > 200 else data
    
    def run_comprehensive_test_suite(self):
        """Run comprehensive test of all 9 MSF MCP tools"""
        print("\n🧪 COMPREHENSIVE MSF MCP TOOLS TEST SUITE")
        print("=" * 70)
        
        # Define all 9 tools with their test parameters
        test_suite = [
            {
                "tool": "get_msf_status",
                "args": {},
                "timeout": 30,
                "description": "Framework status and version information"
            },
            {
                "tool": "execute_msf_command", 
                "args": {"command": "version"},
                "timeout": 45,
                "description": "Basic command execution with version"
            },
            {
                "tool": "search_modules",
                "args": {"query": "ms17_010", "module_type": "exploit"},
                "timeout": 60,
                "description": "Module search with parsing validation"
            },
            {
                "tool": "manage_workspaces",
                "args": {"action": "list"},
                "timeout": 30,
                "description": "Workspace management and listing"
            },
            {
                "tool": "database_operations",
                "args": {"operation": "hosts"},
                "timeout": 30,
                "description": "Database querying capabilities"
            },
            {
                "tool": "session_management",
                "args": {"action": "list"},
                "timeout": 30,
                "description": "Session enumeration and management"
            },
            {
                "tool": "module_operations",
                "args": {"action": "info", "module_path": "auxiliary/scanner/portscan/tcp"},
                "timeout": 60,
                "description": "Module information retrieval (fixed syntax)"
            },
            {
                "tool": "payload_generation",
                "args": {
                    "payload_type": "windows/meterpreter/reverse_tcp",
                    "options": {"LHOST": "127.0.0.1", "LPORT": "4444"},
                    "output_format": "raw"
                },
                "timeout": 90,
                "description": "Payload generation with dual approaches"
            },
            {
                "tool": "resource_script_execution",
                "args": {"script_commands": ["version", "help core"]},
                "timeout": 45,
                "description": "Batch command execution capabilities"
            }
        ]
        
        results = []
        
        for test_case in test_suite:
            print(f"\n{'='*50}")
            print(f"🎯 TEST: {test_case['tool'].upper()}")
            print(f"📝 Description: {test_case['description']}")
            
            result = self.test_individual_tool(
                test_case["tool"],
                test_case["args"],
                test_case["timeout"]
            )
            
            results.append(result)
            
            # Display immediate results
            if result.success:
                print(f"✅ SUCCESS - {result.execution_time:.1f}s - {result.parsing_quality}")
                if result.sample_data:
                    print(f"📊 Sample: {json.dumps(result.sample_data, indent=2)[:300]}...")
            else:
                print(f"❌ FAILED - {result.error_message}")
            
            # Brief pause between tests
            time.sleep(2)
        
        return results
    
    def generate_comprehensive_report(self, results: List[ToolTestResult]):
        """Generate detailed performance report"""
        print("\n" + "="*70)
        print("📊 COMPREHENSIVE MSF MCP PERFORMANCE REPORT")
        print("="*70)
        print(f"🕐 Test Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Total Test Duration: {time.time() - self.start_time:.1f} seconds")
        print(f"🔧 Tools Tested: {len(results)}")
        
        # Overall statistics
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]
        
        print(f"\n📈 OVERALL STATISTICS:")
        print(f"   ✅ Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"   ❌ Failed: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
        
        if successful:
            avg_time = sum(r.execution_time for r in successful) / len(successful)
            print(f"   ⏱️  Average Response Time: {avg_time:.1f} seconds")
            
            structured_responses = len([r for r in successful if r.has_structured_data])
            print(f"   📊 Structured Responses: {structured_responses}/{len(successful)} ({structured_responses/len(successful)*100:.1f}%)")
        
        # Detailed tool results
        print(f"\n🔍 DETAILED TOOL ANALYSIS:")
        print("-"*70)
        
        for result in results:
            status = "✅ PASS" if result.success else "❌ FAIL"
            print(f"\n{status} {result.tool_name.upper()}")
            print(f"   ⏱️  Execution Time: {result.execution_time:.1f}s")
            print(f"   📊 Response Size: {result.response_size} bytes")
            print(f"   🏷️  Parsing Quality: {result.parsing_quality}")
            
            if result.success:
                print(f"   📋 Structured Data: {'Yes' if result.has_structured_data else 'No'}")
                if result.sample_data:
                    sample_str = json.dumps(result.sample_data, indent=2) if isinstance(result.sample_data, (dict, list)) else str(result.sample_data)
                    print(f"   🔬 Sample Data: {sample_str[:150]}{'...' if len(sample_str) > 150 else ''}")
            else:
                print(f"   ❌ Error: {result.error_message}")
        
        # Parsing quality analysis
        print(f"\n🎯 PARSING QUALITY BREAKDOWN:")
        quality_counts = {}
        for result in results:
            quality_counts[result.parsing_quality] = quality_counts.get(result.parsing_quality, 0) + 1
        
        for quality, count in sorted(quality_counts.items()):
            percentage = count / len(results) * 100
            print(f"   {quality}: {count} tools ({percentage:.1f}%)")
        
        # Performance categories
        print(f"\n⚡ PERFORMANCE CATEGORIES:")
        fast_tools = [r for r in successful if r.execution_time < 20]
        medium_tools = [r for r in successful if 20 <= r.execution_time < 45]
        slow_tools = [r for r in successful if r.execution_time >= 45]
        
        print(f"   🚀 Fast (<20s): {len(fast_tools)} tools")
        print(f"   🏃 Medium (20-45s): {len(medium_tools)} tools") 
        print(f"   🐌 Slow (≥45s): {len(slow_tools)} tools")
        
        # Final assessment
        print(f"\n🏆 FINAL ASSESSMENT:")
        success_rate = len(successful) / len(results)
        
        if success_rate >= 0.9:
            assessment = "🎉 EXCELLENT - Production Ready"
        elif success_rate >= 0.75:
            assessment = "✅ GOOD - Minor Issues"
        elif success_rate >= 0.5:
            assessment = "⚠️ NEEDS IMPROVEMENT - Major Issues"
        else:
            assessment = "❌ POOR - Significant Problems"
            
        print(f"   {assessment}")
        print(f"   Success Rate: {success_rate*100:.1f}%")
        
        if len(successful) > 0:
            print(f"   System is {'OPERATIONAL' if success_rate >= 0.5 else 'NOT OPERATIONAL'}")
        
        return {
            "test_timestamp": datetime.now().isoformat(),
            "total_tools": len(results),
            "successful_tools": len(successful),
            "failed_tools": len(failed),
            "success_rate": success_rate,
            "average_response_time": avg_time if successful else 0,
            "tool_results": [
                {
                    "tool": r.tool_name,
                    "success": r.success,
                    "execution_time": r.execution_time,
                    "parsing_quality": r.parsing_quality,
                    "error": r.error_message if not r.success else None
                }
                for r in results
            ]
        }
    
    def cleanup(self):
        """Clean up test resources"""
        if self.process:
            self.process.terminate()
            self.process.wait()

def main():
    """Run comprehensive MSF MCP testing"""
    tester = ComprehensiveMSFTester()
    
    try:
        # Initialize testing environment
        tester.start_mcp_server()
        
        if not tester.initialize_mcp_connection():
            print("❌ Failed to initialize MCP connection - aborting comprehensive test")
            return 1
        
        # Run comprehensive tool testing
        results = tester.run_comprehensive_test_suite()
        
        # Generate detailed report
        report_data = tester.generate_comprehensive_report(results)
        
        # Save detailed results
        with open("comprehensive_test_results.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: comprehensive_test_results.json")
        
        # Return success code based on results
        return 0 if report_data["success_rate"] >= 0.5 else 1
        
    except Exception as e:
        print(f"❌ Comprehensive test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit(main())