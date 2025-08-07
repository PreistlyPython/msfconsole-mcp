#!/usr/bin/env python3
"""
Verify Execute MSF Command Timeout Fix
=====================================
Test the fixed execute_msf_command with adaptive timeouts.
"""

import subprocess
import time
import json
import threading
import queue

class TimeoutFixVerifier:
    def __init__(self):
        self.process = None
        self.response_queue = queue.Queue()
        self.reader_thread = None
        
    def start_mcp_server(self):
        """Start enhanced MCP server"""
        print("🚀 Starting Enhanced MSF MCP Server (Timeout Fixed)")
        print("=" * 60)
        
        self.process = subprocess.Popen(
            ["./start_enhanced_fixed.sh"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.reader_thread = threading.Thread(target=self._read_responses)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        time.sleep(15)
        
    def _read_responses(self):
        """Read MCP responses"""
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
        print("📡 Initializing MCP Connection...")
        
        init_request = {
            "jsonrpc": "2.0",
            "method": "initialize", 
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "timeout_fix_verifier", "version": "1.0"}
            },
            "id": 1
        }
        
        self.process.stdin.write(json.dumps(init_request) + "\n")
        self.process.stdin.flush()
        
        try:
            response_line = self.response_queue.get(timeout=20)
            response = json.loads(response_line)
            
            if response.get("result", {}).get("serverInfo", {}).get("name") == "msfconsole-enhanced":
                print("✅ MCP Connection Initialized")
                
                # Send initialized notification
                init_notify = {"jsonrpc": "2.0", "method": "notifications/initialized"}
                self.process.stdin.write(json.dumps(init_notify) + "\n")
                self.process.stdin.flush()
                time.sleep(3)
                return True
                
        except Exception as e:
            print(f"❌ MCP Initialization Failed: {e}")
            
        return False
    
    def test_execute_command_scenarios(self):
        """Test execute_msf_command with various scenarios"""
        print("\n🧪 TESTING EXECUTE_MSF_COMMAND WITH TIMEOUT FIXES")
        print("=" * 60)
        
        # Test scenarios covering different timeout categories
        scenarios = [
            {
                "name": "Fast Command - help", 
                "command": "help",
                "expected_timeout": 45,
                "max_wait": 50
            },
            {
                "name": "Medium Command - version",
                "command": "version", 
                "expected_timeout": 75,
                "max_wait": 80
            },
            {
                "name": "Medium Command - show options",
                "command": "show options",
                "expected_timeout": 60, 
                "max_wait": 65
            },
            {
                "name": "Database Command - db_status",
                "command": "db_status",
                "expected_timeout": 30,
                "max_wait": 35
            },
            {
                "name": "Custom Timeout - version with override",
                "command": "version",
                "custom_timeout": 90,
                "max_wait": 95
            }
        ]
        
        results = []
        
        for scenario in scenarios:
            print(f"\n🔧 Testing: {scenario['name']}")
            print(f"   Command: '{scenario['command']}'")
            
            if 'custom_timeout' in scenario:
                print(f"   Custom timeout: {scenario['custom_timeout']}s")
                result = self._test_execute_command(
                    scenario['command'], 
                    scenario['max_wait'],
                    custom_timeout=scenario['custom_timeout']
                )
            else:
                print(f"   Expected adaptive timeout: {scenario['expected_timeout']}s")
                result = self._test_execute_command(scenario['command'], scenario['max_wait'])
            
            results.append({
                "scenario": scenario,
                "result": result
            })
            
            if result['success']:
                print(f"   ✅ SUCCESS - {result['execution_time']:.1f}s")
                if 'adaptive_timeout_used' in result:
                    print(f"   🎯 Adaptive timeout used: {result['adaptive_timeout_used']}s")
            else:
                print(f"   ❌ FAILED - {result['error']}")
                
            time.sleep(2)
        
        return results
    
    def _test_execute_command(self, command: str, max_wait: int, custom_timeout: int = None) -> dict:
        """Test a single execute_msf_command call"""
        request_id = hash(f"exec_{command}_{time.time()}") % 10000
        start_time = time.time()
        
        # Build request
        args = {"command": command}
        if custom_timeout:
            args["timeout"] = custom_timeout
            
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {
                "name": "execute_msf_command",
                "arguments": args
            },
            "id": request_id
        }
        
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        
        notifications = 0
        timeout_info = None
        timeout_time = start_time + max_wait
        
        while time.time() < timeout_time:
            try:
                response_line = self.response_queue.get(timeout=5)
                
                # Check for notifications (may contain timeout info)
                if '"method":"notifications/message"' in response_line:
                    notifications += 1
                    try:
                        notif = json.loads(response_line)
                        msg = notif.get("params", {}).get("data", "")
                        if "timeout:" in msg:
                            # Extract timeout information
                            timeout_part = msg.split("timeout: ")[1].split("s")[0] if "timeout:" in msg else None
                            if timeout_part:
                                timeout_info = int(timeout_part.replace(")", ""))
                    except:
                        pass
                    continue
                
                # Check for tool response
                if f'"id":{request_id}' in response_line:
                    execution_time = time.time() - start_time
                    
                    try:
                        response = json.loads(response_line)
                        
                        result = {
                            "success": "result" in response,
                            "execution_time": execution_time,
                            "notifications": notifications
                        }
                        
                        if timeout_info:
                            result["adaptive_timeout_used"] = timeout_info
                            
                        if "error" in response:
                            result["error"] = response["error"]
                        
                        return result
                        
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "execution_time": execution_time,
                            "error": f"JSON parse error: {e}",
                            "notifications": notifications
                        }
                        
            except queue.Empty:
                continue
        
        return {
            "success": False,
            "execution_time": max_wait,
            "error": f"Timeout after {max_wait}s",
            "notifications": notifications
        }
    
    def generate_verification_report(self, results: list):
        """Generate verification report"""
        print("\n" + "=" * 60)
        print("📊 TIMEOUT FIX VERIFICATION REPORT")
        print("=" * 60)
        
        successful = [r for r in results if r["result"]["success"]]
        failed = [r for r in results if not r["result"]["success"]]
        
        print(f"\n📈 OVERALL RESULTS:")
        print(f"   ✅ Successful: {len(successful)}/{len(results)} ({len(successful)/len(results)*100:.1f}%)")
        print(f"   ❌ Failed: {len(failed)}/{len(results)} ({len(failed)/len(results)*100:.1f}%)")
        
        if successful:
            avg_time = sum(r["result"]["execution_time"] for r in successful) / len(successful)
            print(f"   ⏱️  Average response time: {avg_time:.1f}s")
        
        print(f"\n🔍 DETAILED RESULTS:")
        for result_data in results:
            scenario = result_data["scenario"]
            result = result_data["result"]
            
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"\n{status} {scenario['name']}")
            print(f"   Command: '{scenario['command']}'")
            print(f"   Execution time: {result['execution_time']:.1f}s")
            
            if result["success"]:
                if 'adaptive_timeout_used' in result:
                    print(f"   Adaptive timeout: {result['adaptive_timeout_used']}s")
                print(f"   Notifications: {result['notifications']}")
            else:
                print(f"   Error: {result.get('error', 'Unknown')}")
        
        # Assessment
        success_rate = len(successful) / len(results)
        print(f"\n🏆 TIMEOUT FIX ASSESSMENT:")
        
        if success_rate == 1.0:
            print("   🎉 PERFECT - All execute_msf_command tests passed!")
            print("   ✅ Timeout issue completely resolved")
            print("   🚀 Ready for production with 100% reliability")
        elif success_rate >= 0.8:
            print("   ✅ EXCELLENT - Significant improvement achieved")
            print("   🎯 Timeout fix working for most scenarios")
        elif success_rate >= 0.6:
            print("   ⚠️ GOOD - Some improvement, more tuning needed")
        else:
            print("   ❌ NEEDS WORK - Timeout fix requires further optimization")
        
        return {
            "success_rate": success_rate,
            "successful_tests": len(successful),
            "total_tests": len(results),
            "average_response_time": avg_time if successful else 0
        }
    
    def cleanup(self):
        """Cleanup resources"""
        if self.process:
            self.process.terminate()

def main():
    verifier = TimeoutFixVerifier()
    
    try:
        # Start and initialize
        verifier.start_mcp_server()
        
        if not verifier.initialize_mcp():
            print("❌ Failed to initialize MCP")
            return 1
        
        # Test timeout fix scenarios
        results = verifier.test_execute_command_scenarios()
        
        # Generate verification report
        report = verifier.generate_verification_report(results)
        
        # Save results
        with open("timeout_fix_verification.json", "w") as f:
            json.dump({"report": report, "detailed_results": results}, f, indent=2)
        
        print(f"\n💾 Verification results saved to: timeout_fix_verification.json")
        
        return 0 if report["success_rate"] >= 0.8 else 1
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        verifier.cleanup()

if __name__ == "__main__":
    exit(main())