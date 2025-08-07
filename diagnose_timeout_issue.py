#!/usr/bin/env python3
"""
MSF MCP Execute Command Timeout Diagnostic Tool
===============================================
Systematic diagnosis of why execute_msf_command is timing out while other tools work.
"""

import subprocess
import time
import json
import threading
import queue
import os
import psutil
from typing import Dict, List, Any
from datetime import datetime

class TimeoutDiagnostic:
    def __init__(self):
        self.process = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        self.diagnostic_data = {}
        
    def start_mcp_server(self):
        """Start MCP server with enhanced monitoring"""
        print("🔍 Starting MSF MCP Server for Timeout Diagnosis")
        print("=" * 60)
        
        # Monitor system resources before start
        print("📊 System Resources Before Startup:")
        self._log_system_resources("startup")
        
        self.process = subprocess.Popen(
            ["./start_enhanced_fixed.sh"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor MSF processes
        self._monitor_msf_processes()
        
        # Start response monitoring
        self.reader_thread = threading.Thread(target=self._read_responses_with_timing)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        print("⏳ Monitoring server initialization (15 seconds)...")
        time.sleep(15)
        
    def _log_system_resources(self, phase: str):
        """Log system resource usage"""
        try:
            memory = psutil.virtual_memory()
            cpu = psutil.cpu_percent(interval=1)
            disk = psutil.disk_usage('/')
            
            resources = {
                "phase": phase,
                "timestamp": datetime.now().isoformat(),
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "cpu_percent": cpu,
                "disk_free_gb": disk.free / (1024**3)
            }
            
            print(f"   💾 Memory: {memory.percent:.1f}% used, {memory.available/(1024**3):.1f}GB available")
            print(f"   🖥️  CPU: {cpu:.1f}% usage")
            print(f"   💽 Disk: {disk.free/(1024**3):.1f}GB free")
            
            self.diagnostic_data[f"resources_{phase}"] = resources
            
        except Exception as e:
            print(f"   ⚠️ Resource monitoring error: {e}")
    
    def _monitor_msf_processes(self):
        """Monitor MSF-related processes"""
        print("🔍 Monitoring MSF Processes:")
        
        msf_processes = []
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                if any(keyword in ' '.join(proc.info['cmdline'] or []).lower() 
                      for keyword in ['msfconsole', 'msfrpcd', 'metasploit', 'postgresql']):
                    msf_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmdline': ' '.join(proc.info['cmdline'] or []),
                        'memory_mb': proc.info['memory_info'].rss / (1024*1024) if proc.info['memory_info'] else 0
                    })
            
            print(f"   Found {len(msf_processes)} MSF-related processes")
            for proc in msf_processes:
                print(f"   PID {proc['pid']}: {proc['name']} ({proc['memory_mb']:.1f}MB)")
                
            self.diagnostic_data["msf_processes"] = msf_processes
            
        except Exception as e:
            print(f"   ⚠️ Process monitoring error: {e}")
    
    def _read_responses_with_timing(self):
        """Read responses with detailed timing analysis"""
        response_times = []
        
        try:
            while True:
                start_time = time.time()
                line = self.process.stdout.readline()
                read_time = time.time() - start_time
                
                if not line:
                    break
                    
                response_times.append(read_time)
                self.response_queue.put({
                    "content": line.strip(),
                    "read_time": read_time,
                    "timestamp": time.time()
                })
                
        except Exception as e:
            self.response_queue.put({
                "content": f"READER_ERROR: {e}",
                "read_time": 0,
                "timestamp": time.time()
            })
        
        self.diagnostic_data["response_times"] = response_times
    
    def initialize_mcp_connection(self):
        """Initialize MCP with detailed timing"""
        print("📡 Initializing MCP Connection with Timing Analysis...")
        
        init_start = time.time()
        
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "timeout_diagnostic", "version": "1.0"}
            },
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        try:
            response_data = self.response_queue.get(timeout=20)
            init_time = time.time() - init_start
            
            response = json.loads(response_data["content"])
            server_name = response.get("result", {}).get("serverInfo", {}).get("name")
            
            print(f"✅ MCP Initialized in {init_time:.2f}s")
            print(f"   Server: {server_name}")
            print(f"   Response read time: {response_data['read_time']:.3f}s")
            
            self.diagnostic_data["init_time"] = init_time
            
            # Send initialized notification
            init_notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
            self.process.stdin.write(json.dumps(init_notify) + "\n")
            self.process.stdin.flush()
            time.sleep(3)
            
            return True
            
        except Exception as e:
            print(f"❌ MCP Initialization Failed: {e}")
            return False
    
    def diagnose_execute_msf_command_detailed(self):
        """Detailed diagnosis of execute_msf_command timeout"""
        print("\n🔬 DETAILED EXECUTE_MSF_COMMAND TIMEOUT DIAGNOSIS")
        print("=" * 60)
        
        # Test with different commands and timeouts
        test_scenarios = [
            {"command": "help", "timeout": 30, "description": "Simple help command"},
            {"command": "version", "timeout": 60, "description": "Version command (original test)"},
            {"command": "show options", "timeout": 45, "description": "Show global options"},
            {"command": "db_status", "timeout": 30, "description": "Database status check"}
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing Scenario: {scenario['description']}")
            print(f"   Command: '{scenario['command']}'")
            print(f"   Timeout: {scenario['timeout']}s")
            
            result = self._test_execute_command_with_monitoring(
                scenario['command'], 
                scenario['timeout']
            )
            
            results.append({
                "scenario": scenario,
                "result": result
            })
            
            if result['success']:
                print(f"   ✅ SUCCESS - {result['execution_time']:.1f}s")
            else:
                print(f"   ❌ FAILED - {result['error']}")
                print(f"   📊 Notifications: {result['notifications_received']}")
                print(f"   ⏱️  Phases: {result['timing_phases']}")
            
            # Brief pause between tests
            time.sleep(3)
        
        return results
    
    def _test_execute_command_with_monitoring(self, command: str, timeout: int) -> Dict:
        """Test execute_msf_command with detailed monitoring"""
        request_id = hash(f"exec_{command}_{time.time()}") % 10000
        start_time = time.time()
        
        # Log resources before command
        self._log_system_resources(f"before_{command.replace(' ', '_')}")
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "execute_msf_command",
                "arguments": {"command": command}
            },
            "id": request_id
        }
        
        # Send request with timing
        send_time = time.time()
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        write_time = time.time() - send_time
        
        # Monitor response with detailed phases
        phases = {
            "request_sent": time.time() - start_time,
            "first_notification": None,
            "last_notification": None,
            "response_received": None
        }
        
        notifications_received = 0
        notification_types = []
        timeout_time = start_time + timeout
        
        while time.time() < timeout_time:
            try:
                response_data = self.response_queue.get(timeout=5)
                response_time = time.time() - start_time
                
                # Parse response
                if '"method":"notifications/' in response_data["content"]:
                    notifications_received += 1
                    
                    if phases["first_notification"] is None:
                        phases["first_notification"] = response_time
                    phases["last_notification"] = response_time
                    
                    # Extract notification type
                    try:
                        notif = json.loads(response_data["content"])
                        notif_method = notif.get("method", "unknown")
                        notification_types.append(notif_method)
                    except:
                        notification_types.append("parse_error")
                    
                    continue
                
                # Check for tool response
                if f'"id":{request_id}' in response_data["content"]:
                    execution_time = time.time() - start_time
                    phases["response_received"] = execution_time
                    
                    try:
                        response = json.loads(response_data["content"])
                        
                        # Log resources after command
                        self._log_system_resources(f"after_{command.replace(' ', '_')}")
                        
                        if "result" in response:
                            return {
                                "success": True,
                                "execution_time": execution_time,
                                "notifications_received": notifications_received,
                                "notification_types": notification_types,
                                "timing_phases": phases,
                                "write_time": write_time,
                                "response_size": len(response_data["content"])
                            }
                        else:
                            return {
                                "success": False,
                                "execution_time": execution_time,
                                "error": "Invalid response format",
                                "notifications_received": notifications_received,
                                "notification_types": notification_types,
                                "timing_phases": phases
                            }
                            
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "execution_time": time.time() - start_time,
                            "error": f"JSON parse error: {e}",
                            "notifications_received": notifications_received,
                            "timing_phases": phases
                        }
                
            except queue.Empty:
                continue
        
        # Timeout occurred
        final_time = time.time() - start_time
        return {
            "success": False,
            "execution_time": final_time,
            "error": "Timeout - no response received",
            "notifications_received": notifications_received,
            "notification_types": notification_types,
            "timing_phases": phases,
            "timeout_reached": True
        }
    
    def analyze_other_working_tools(self):
        """Compare with working tools to find differences"""
        print("\n🔍 COMPARATIVE ANALYSIS WITH WORKING TOOLS")
        print("=" * 60)
        
        # Test a known working tool for comparison
        working_tools = [
            {"name": "get_msf_status", "args": {}},
            {"name": "manage_workspaces", "args": {"action": "list"}}
        ]
        
        for tool in working_tools:
            print(f"\n📊 Testing Working Tool: {tool['name']}")
            
            result = self._test_tool_with_monitoring(tool['name'], tool['args'], 30)
            
            if result['success']:
                print(f"   ✅ SUCCESS - {result['execution_time']:.1f}s")
                print(f"   📡 Notifications: {result['notifications_received']}")
                print(f"   ⏱️  First notification: {result['timing_phases'].get('first_notification', 'N/A'):.1f}s")
            else:
                print(f"   ❌ UNEXPECTED FAILURE: {result['error']}")
    
    def _test_tool_with_monitoring(self, tool_name: str, args: Dict, timeout: int) -> Dict:
        """Test any tool with monitoring"""
        request_id = hash(f"{tool_name}_{time.time()}") % 10000
        start_time = time.time()
        
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": args
            },
            "id": request_id
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        phases = {"first_notification": None, "response_received": None}
        notifications_received = 0
        timeout_time = start_time + timeout
        
        while time.time() < timeout_time:
            try:
                response_data = self.response_queue.get(timeout=5)
                response_time = time.time() - start_time
                
                if '"method":"notifications/' in response_data["content"]:
                    notifications_received += 1
                    if phases["first_notification"] is None:
                        phases["first_notification"] = response_time
                    continue
                
                if f'"id":{request_id}' in response_data["content"]:
                    phases["response_received"] = response_time
                    
                    try:
                        response = json.loads(response_data["content"])
                        return {
                            "success": "result" in response,
                            "execution_time": response_time,
                            "notifications_received": notifications_received,
                            "timing_phases": phases
                        }
                    except:
                        return {
                            "success": False,
                            "execution_time": response_time,
                            "error": "JSON parse error",
                            "notifications_received": notifications_received,
                            "timing_phases": phases
                        }
                        
            except queue.Empty:
                continue
        
        return {
            "success": False,
            "execution_time": timeout,
            "error": "Timeout",
            "notifications_received": notifications_received,
            "timing_phases": phases
        }
    
    def generate_diagnostic_report(self, test_results: List[Dict]):
        """Generate comprehensive diagnostic report"""
        print("\n" + "=" * 60)
        print("📋 TIMEOUT DIAGNOSTIC REPORT")
        print("=" * 60)
        
        print(f"🕐 Diagnostic Session: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # System resources analysis
        print(f"\n💻 SYSTEM RESOURCES ANALYSIS:")
        if "resources_startup" in self.diagnostic_data:
            startup_res = self.diagnostic_data["resources_startup"]
            print(f"   Memory Usage: {startup_res['memory_percent']:.1f}%")
            print(f"   Available Memory: {startup_res['memory_available_gb']:.1f}GB")
            print(f"   CPU Usage: {startup_res['cpu_percent']:.1f}%")
        
        # MSF processes analysis
        print(f"\n🔍 MSF PROCESSES ANALYSIS:")
        if "msf_processes" in self.diagnostic_data:
            processes = self.diagnostic_data["msf_processes"]
            print(f"   Total MSF processes: {len(processes)}")
            total_memory = sum(p['memory_mb'] for p in processes)
            print(f"   Total MSF memory usage: {total_memory:.1f}MB")
        
        # Test results analysis
        print(f"\n🧪 EXECUTE_MSF_COMMAND TEST ANALYSIS:")
        for i, test in enumerate(test_results, 1):
            scenario = test["scenario"]
            result = test["result"]
            
            print(f"\n   Test {i}: {scenario['description']}")
            print(f"   Command: '{scenario['command']}'")
            
            if result["success"]:
                print(f"   ✅ SUCCESS ({result['execution_time']:.1f}s)")
            else:
                print(f"   ❌ FAILED: {result['error']}")
                print(f"   📊 Notifications received: {result['notifications_received']}")
                
                phases = result.get('timing_phases', {})
                if phases.get('first_notification'):
                    print(f"   ⏱️  First notification: {phases['first_notification']:.1f}s")
                if phases.get('last_notification'):
                    print(f"   ⏱️  Last notification: {phases['last_notification']:.1f}s")
                
                if 'notification_types' in result and result['notification_types']:
                    print(f"   📡 Notification types: {set(result['notification_types'])}")
        
        # Root cause analysis
        print(f"\n🎯 ROOT CAUSE ANALYSIS:")
        
        successful_tests = [t for t in test_results if t["result"]["success"]]
        failed_tests = [t for t in test_results if not t["result"]["success"]]
        
        if successful_tests:
            avg_success_time = sum(t["result"]["execution_time"] for t in successful_tests) / len(successful_tests)
            print(f"   ✅ Successful commands average: {avg_success_time:.1f}s")
        
        if failed_tests:
            print(f"   ❌ Failed commands: {len(failed_tests)}/{len(test_results)}")
            
            # Analyze notification patterns
            all_notifications = []
            for test in failed_tests:
                all_notifications.extend(test["result"].get("notifications_received", 0))
            
            if any(t["result"]["notifications_received"] > 0 for t in failed_tests):
                print(f"   📊 Server is responding (notifications received)")
                print(f"   🔍 Issue likely: MSF command execution hanging, not MCP protocol")
            else:
                print(f"   📊 No notifications received - potential MCP protocol issue")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if failed_tests:
            failing_commands = [t["scenario"]["command"] for t in failed_tests]
            print(f"   🎯 Failing commands: {failing_commands}")
            
            if any("version" in cmd for cmd in failing_commands):
                print(f"   🔧 Version command issue - likely MSF initialization delay")
                print(f"   📈 Recommend: Increase timeout to 90-120s for execute_msf_command")
                print(f"   🚀 Alternative: Pre-warm MSF console before first execution")
            
            if all(t["result"]["notifications_received"] > 0 for t in failed_tests):
                print(f"   ✅ MCP protocol working correctly")
                print(f"   🐌 Issue: MSF console command execution is slow/hanging")
                print(f"   🔧 Solutions:")
                print(f"      1. Increase execute_msf_command timeout to 90-120s")
                print(f"      2. Optimize MSF initialization process")
                print(f"      3. Pre-initialize MSF console in background")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "test_results": test_results,
            "diagnostic_data": self.diagnostic_data,
            "success_rate": len(successful_tests) / len(test_results) if test_results else 0
        }
    
    def cleanup(self):
        """Clean up diagnostic resources"""
        if self.process:
            self.process.terminate()

def main():
    """Run timeout diagnostic analysis"""
    diagnostic = TimeoutDiagnostic()
    
    try:
        # Start server and initialize
        diagnostic.start_mcp_server()
        
        if not diagnostic.initialize_mcp_connection():
            print("❌ Failed to initialize MCP - cannot diagnose timeout")
            return 1
        
        # Run detailed execute_msf_command diagnosis
        test_results = diagnostic.diagnose_execute_msf_command_detailed()
        
        # Compare with working tools
        diagnostic.analyze_other_working_tools()
        
        # Generate comprehensive report
        report = diagnostic.generate_diagnostic_report(test_results)
        
        # Save diagnostic data
        with open("timeout_diagnostic_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n💾 Diagnostic report saved to: timeout_diagnostic_report.json")
        
        return 0
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        diagnostic.cleanup()

if __name__ == "__main__":
    exit(main())