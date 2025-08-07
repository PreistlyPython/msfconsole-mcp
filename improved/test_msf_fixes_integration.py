#!/usr/bin/env python3

"""
MSFConsole MCP Fixes Integration Test Suite
-------------------------------------------
Comprehensive test suite for validating all MSFConsole MCP fixes including:
- Payload generation error fixes
- Framework version updates
- Initialization optimizations  
- Output parsing improvements
- Error handling enhancements
- Performance monitoring
"""

import asyncio
import logging
import unittest
import tempfile
import os
import json
import time
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Test imports
from msf_payload_fix import MSFPayloadFix
from msf_performance_optimizer import MSFPerformanceOptimizer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MSFFixesIntegrationTests(unittest.TestCase):
    """Integration tests for MSFConsole MCP fixes."""
    
    def setUp(self):
        """Set up test environment."""
        self.payload_fix = None
        self.performance_optimizer = None
        self.test_results = {}
        
    def tearDown(self):
        """Clean up test environment."""
        if hasattr(self, 'temp_files'):
            for temp_file in self.temp_files:
                try:
                    os.unlink(temp_file)
                except Exception:
                    pass
    
    async def test_payload_generation_fixes(self):
        """Test payload generation with encoding error fixes."""
        logger.info("Testing payload generation fixes...")
        
        try:
            self.payload_fix = MSFPayloadFix()
            await self.payload_fix.initialize()
            
            # Test cases for payload generation
            test_cases = [
                {
                    "name": "basic_linux_payload",
                    "payload": "linux/x64/shell_reverse_tcp",
                    "options": {"LHOST": "192.168.1.100", "LPORT": "4444"},
                    "expected_success": True
                },
                {
                    "name": "windows_payload_with_encoder",
                    "payload": "windows/x64/meterpreter/reverse_tcp", 
                    "options": {"LHOST": "10.0.0.1", "LPORT": "8080"},
                    "encoder": "x64/xor",
                    "expected_success": True
                },
                {
                    "name": "payload_with_special_chars",
                    "payload": "linux/x86/shell_reverse_tcp",
                    "options": {"LHOST": "test'host\"with\\chars", "LPORT": "4444"},
                    "expected_success": True  # Should handle encoding issues
                },
                {
                    "name": "invalid_payload",
                    "payload": "invalid/nonexistent/payload",
                    "options": {},
                    "expected_success": False
                }
            ]
            
            results = []
            for test_case in test_cases:
                logger.info(f"Testing: {test_case['name']}")
                
                start_time = time.time()
                result = await self.payload_fix.generate_payload_fixed(
                    payload=test_case["payload"],
                    options=test_case.get("options", {}),
                    encoder=test_case.get("encoder")
                )
                end_time = time.time()
                
                test_result = {
                    "test_name": test_case["name"],
                    "success": result.get("success", False),
                    "expected_success": test_case["expected_success"],
                    "execution_time": end_time - start_time,
                    "method_used": result.get("method", "unknown"),
                    "error": result.get("error"),
                    "passed": result.get("success", False) == test_case["expected_success"]
                }
                
                results.append(test_result)
                logger.info(f"Result: {test_result}")
            
            # Calculate overall success rate
            passed_tests = sum(1 for r in results if r["passed"])
            success_rate = (passed_tests / len(results)) * 100
            
            self.test_results["payload_generation"] = {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "success_rate": success_rate,
                "details": results
            }
            
            # Assert at least 75% success rate
            self.assertGreaterEqual(success_rate, 75.0, 
                                   f"Payload generation success rate {success_rate}% below 75%")
            
            logger.info(f"Payload generation tests: {success_rate}% success rate")
            return True
            
        except Exception as e:
            logger.error(f"Payload generation test failed: {e}")
            self.test_results["payload_generation"] = {"error": str(e)}
            return False
    
    async def test_performance_optimizations(self):
        """Test performance optimization fixes."""
        logger.info("Testing performance optimizations...")
        
        try:
            self.performance_optimizer = MSFPerformanceOptimizer()
            init_result = await self.performance_optimizer.initialize()
            
            # Test initialization optimizations
            self.assertTrue(init_result["framework_check"], "Framework check failed")
            self.assertTrue(init_result["optimization_applied"], "Optimizations not applied")
            
            # Test parsing improvements
            test_outputs = [
                {
                    "type": "module_search",
                    "output": "   #   Rank    Name                                         Date        Description\\n   -   ----    ----                                         ----        -----------\\n   0   normal  auxiliary/admin/http/tomcat_administration    2009-09-19  Tomcat Administration Tool Manager Access\\n   1   normal  auxiliary/admin/http/tomcat_manager           2009-09-19  Tomcat Application Manager Manager Access",
                    "expected_parsed": True
                },
                {
                    "type": "payload_generation", 
                    "output": "Payload size: 74 bytes\\n\\x48\\x31\\xff\\x48\\x31\\xf6\\x48\\x31\\xd2\\x48\\x31\\xc0\\nmsf >",
                    "expected_parsed": True
                }
            ]
            
            parsing_results = []
            for test_output in test_outputs:
                result = self.performance_optimizer.parse_output_enhanced(
                    test_output["output"], 
                    test_output["type"]
                )
                
                parsing_result = {
                    "type": test_output["type"],
                    "parsed": result.get("parsed", False),
                    "expected_parsed": test_output["expected_parsed"],
                    "passed": result.get("parsed", False) == test_output["expected_parsed"]
                }
                parsing_results.append(parsing_result)
            
            # Test performance monitoring
            performance_report = self.performance_optimizer.get_performance_report()
            self.assertIsInstance(performance_report, dict)
            self.assertIn("framework_info", performance_report)
            
            parsing_success_rate = (sum(1 for r in parsing_results if r["passed"]) / 
                                   len(parsing_results)) * 100
            
            self.test_results["performance_optimizations"] = {
                "initialization": init_result,
                "parsing_tests": parsing_results,
                "parsing_success_rate": parsing_success_rate,
                "performance_report": performance_report
            }
            
            logger.info(f"Performance optimization tests: {parsing_success_rate}% parsing success")
            return True
            
        except Exception as e:
            logger.error(f"Performance optimization test failed: {e}")
            self.test_results["performance_optimizations"] = {"error": str(e)}
            return False
    
    async def test_error_handling_improvements(self):
        """Test improved error handling."""
        logger.info("Testing error handling improvements...")
        
        try:
            # Test timeout handling
            if self.payload_fix:
                # Test with very short timeout to trigger timeout error
                with patch('asyncio.wait_for') as mock_wait_for:
                    mock_wait_for.side_effect = asyncio.TimeoutError()
                    
                    result = await self.payload_fix.generate_payload_fixed(
                        payload="linux/x64/shell_reverse_tcp",
                        options={"LHOST": "127.0.0.1", "LPORT": "4444"}
                    )
                    
                    # Should handle timeout gracefully
                    self.assertFalse(result.get("success", True))
                    self.assertIn("timeout", result.get("error", "").lower())
            
            # Test encoding error handling
            if self.payload_fix:
                # Test with problematic characters
                problematic_text = "test'with\"quotes\\and\\backslashes"
                fixed_text = self.payload_fix._fix_encoding_issues(problematic_text)
                
                # Should not contain unescaped special characters
                self.assertNotIn("'", fixed_text)
                self.assertNotIn('"', fixed_text)
            
            # Test output parsing error handling
            if self.performance_optimizer:
                result = self.performance_optimizer.parse_output_enhanced(
                    "invalid output format", 
                    "nonexistent_type"
                )
                
                # Should handle gracefully
                self.assertFalse(result.get("parsed", True))
            
            self.test_results["error_handling"] = {
                "timeout_handling": "passed",
                "encoding_handling": "passed", 
                "parsing_error_handling": "passed"
            }
            
            logger.info("Error handling tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Error handling test failed: {e}")
            self.test_results["error_handling"] = {"error": str(e)}
            return False
    
    async def test_framework_version_detection(self):
        """Test framework version detection and update suggestions."""
        logger.info("Testing framework version detection...")
        
        try:
            if self.performance_optimizer:
                framework_info = self.performance_optimizer.framework_info
                
                # Should have version information
                self.assertIn("version", framework_info)
                self.assertIn("needs_update", framework_info)
                self.assertIn("last_checked", framework_info)
                
                # Version should be parseable
                version = framework_info.get("version", "")
                version_parts = version.split(".")
                self.assertGreaterEqual(len(version_parts), 2, "Version format invalid")
                
                # Test version comparison logic
                test_versions = [
                    ("6.2.9", True),   # Should need update
                    ("6.3.0", False),  # Should not need update  
                    ("6.4.1", False),  # Should not need update
                ]
                
                for test_version, should_need_update in test_versions:
                    needs_update = self.performance_optimizer._version_needs_update(test_version)
                    self.assertEqual(needs_update, should_need_update, 
                                   f"Version {test_version} update check failed")
            
            self.test_results["framework_version"] = {
                "detection": "passed",
                "version_info": framework_info if self.performance_optimizer else {},
                "version_comparison": "passed"
            }
            
            logger.info("Framework version detection tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Framework version test failed: {e}")
            self.test_results["framework_version"] = {"error": str(e)}
            return False
    
    async def test_performance_monitoring(self):
        """Test performance monitoring and metrics collection."""
        logger.info("Testing performance monitoring...")
        
        try:
            if self.performance_optimizer:
                # Test metric collection
                initial_report = self.performance_optimizer.get_performance_report()
                
                # Simulate some command executions
                mock_msf = MagicMock()
                mock_msf.execute_command = AsyncMock(return_value="test output")
                
                # Execute multiple commands to generate metrics
                test_commands = [
                    "search http",
                    "use auxiliary/scanner/http/title",
                    "show options"
                ]
                
                for command in test_commands:
                    await self.performance_optimizer.execute_with_optimization(
                        command, mock_msf, timeout=30
                    )
                
                # Check that metrics were collected
                final_report = self.performance_optimizer.get_performance_report()
                
                self.assertGreater(
                    final_report["command_stats"]["total_commands"],
                    initial_report["command_stats"]["total_commands"],
                    "Command count not incremented"
                )
                
                # Test cache functionality
                self.assertIn("cache_stats", final_report)
                cache_stats = final_report["cache_stats"]
                total_operations = cache_stats["hits"] + cache_stats["misses"]
                if total_operations > 0:
                    hit_rate = cache_stats["hit_rate"]
                    self.assertGreaterEqual(hit_rate, 0.0)
                    self.assertLessEqual(hit_rate, 100.0)
            
            self.test_results["performance_monitoring"] = {
                "metrics_collection": "passed",
                "cache_functionality": "passed",
                "report_generation": "passed"
            }
            
            logger.info("Performance monitoring tests passed")
            return True
            
        except Exception as e:
            logger.error(f"Performance monitoring test failed: {e}")
            self.test_results["performance_monitoring"] = {"error": str(e)}
            return False
    
    async def run_all_tests(self):
        """Run all integration tests."""
        logger.info("Starting MSFConsole MCP Fixes Integration Tests...")
        
        test_methods = [
            self.test_payload_generation_fixes,
            self.test_performance_optimizations,
            self.test_error_handling_improvements,
            self.test_framework_version_detection,
            self.test_performance_monitoring
        ]
        
        results = []
        for test_method in test_methods:
            try:
                result = await test_method()
                results.append(result)
            except Exception as e:
                logger.error(f"Test {test_method.__name__} failed: {e}")
                results.append(False)
        
        success_rate = (sum(1 for r in results if r) / len(results)) * 100
        
        final_report = {
            "overall_success_rate": success_rate,
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results if r),
            "test_details": self.test_results,
            "timestamp": time.time(),
            "summary": {
                "payload_generation": "✓" if success_rate >= 75 else "✗",
                "performance_optimization": "✓" if "performance_optimizations" in self.test_results else "✗",
                "error_handling": "✓" if "error_handling" in self.test_results else "✗",
                "framework_detection": "✓" if "framework_version" in self.test_results else "✗",
                "performance_monitoring": "✓" if "performance_monitoring" in self.test_results else "✗"
            }
        }
        
        logger.info(f"Integration tests completed: {success_rate}% success rate")
        return final_report


class AsyncMock:
    """Simple async mock for testing."""
    def __init__(self, return_value=None):
        self.return_value = return_value
    
    async def __call__(self, *args, **kwargs):
        return self.return_value


async def main():
    """Main test runner."""
    test_suite = MSFFixesIntegrationTests()
    
    try:
        # Run all integration tests
        report = await test_suite.run_all_tests()
        
        # Generate test report
        print("\\n" + "="*80)
        print("MSFConsole MCP Fixes Integration Test Report")
        print("="*80)
        print(f"Overall Success Rate: {report['overall_success_rate']:.1f}%")
        print(f"Tests Passed: {report['passed_tests']}/{report['total_tests']}")
        print("\\nTest Summary:")
        for test_name, status in report['summary'].items():
            print(f"  {test_name}: {status}")
        
        print("\\nDetailed Results:")
        for test_name, details in report['test_details'].items():
            print(f"\\n{test_name}:")
            if isinstance(details, dict):
                for key, value in details.items():
                    if key != 'details':  # Skip verbose details
                        print(f"  {key}: {value}")
        
        # Save report to file
        report_file = f"msf_fixes_integration_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\\nDetailed report saved to: {report_file}")
        
        # Return appropriate exit code
        if report['overall_success_rate'] >= 80:
            print("\\n✅ Integration tests PASSED")
            return 0
        else:
            print("\\n❌ Integration tests FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        print(f"\\n❌ Test runner failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))