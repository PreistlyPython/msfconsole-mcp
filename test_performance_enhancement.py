#!/usr/bin/env python3

"""
MSFConsole Performance Enhancement Testing
-----------------------------------------
Test and validate performance improvements from the optimizer.
"""

import asyncio
import time
import json
import logging
from msf_performance_enhancer import MSFConsoleOptimizer, create_msf_optimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceComparisonTest:
    """Compare performance before and after optimization."""
    
    def __init__(self):
        self.optimizer = None
        self.baseline_results = {}
        self.optimized_results = {}
    
    async def run_comparison_test(self):
        """Run comprehensive performance comparison."""
        logger.info("Starting performance comparison test...")
        
        # Test without optimization (baseline)
        logger.info("Running baseline tests...")
        await self._run_baseline_tests()
        
        # Test with optimization
        logger.info("Running optimized tests...")
        self.optimizer = create_msf_optimizer()
        await self.optimizer.start_optimization()
        
        try:
            await self._run_optimized_tests()
        finally:
            if self.optimizer:
                await self.optimizer.stop_optimization()
        
        # Generate comparison report
        return self._generate_comparison_report()
    
    async def _run_baseline_tests(self):
        """Run baseline performance tests."""
        import subprocess
        
        test_cases = [
            ("version_check", ["msfconsole", "--version"]),
            ("quick_help", ["msfconsole", "-q", "-x", "help; exit"]),
            ("db_status", ["msfconsole", "-q", "-x", "db_status; exit"])
        ]
        
        for test_name, command in test_cases:
            try:
                start_time = time.time()
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                execution_time = time.time() - start_time
                
                self.baseline_results[test_name] = {
                    "execution_time": execution_time,
                    "success": result.returncode == 0,
                    "output_size": len(result.stdout),
                    "error": result.stderr if result.returncode != 0 else None
                }
                
                logger.info(f"Baseline {test_name}: {execution_time:.2f}s")
                
            except subprocess.TimeoutExpired:
                self.baseline_results[test_name] = {
                    "execution_time": 30.0,
                    "success": False,
                    "output_size": 0,
                    "error": "Timeout"
                }
                logger.warning(f"Baseline {test_name}: Timeout")
            except Exception as e:
                self.baseline_results[test_name] = {
                    "execution_time": 0,
                    "success": False,
                    "output_size": 0,
                    "error": str(e)
                }
                logger.error(f"Baseline {test_name}: Error - {e}")
    
    async def _run_optimized_tests(self):
        """Run optimized performance tests."""
        test_cases = [
            ("version_check", "version"),
            ("quick_help", "help"),
            ("db_status", "db_status"),
            ("module_search", "search exploit platform:windows"),
            ("payload_gen", None)  # Special case for payload generation
        ]
        
        for test_name, command in test_cases:
            try:
                if test_name == "payload_gen":
                    # Test optimized payload generation
                    start_time = time.time()
                    result = await self.optimizer.optimized_payload_generation(
                        "windows/meterpreter/reverse_tcp",
                        {"LHOST": "127.0.0.1", "LPORT": "4444"}
                    )
                    execution_time = time.time() - start_time
                    
                    self.optimized_results[test_name] = {
                        "execution_time": execution_time,
                        "success": result["success"],
                        "output_size": result["size_bytes"],
                        "error": result.get("error")
                    }
                else:
                    # Test optimized command execution
                    result = await self.optimizer.optimized_command_execution(command)
                    
                    self.optimized_results[test_name] = {
                        "execution_time": result["execution_time"],
                        "success": result["success"],
                        "output_size": len(result["stdout"]),
                        "error": result["stderr"] if not result["success"] else None
                    }
                
                logger.info(f"Optimized {test_name}: {self.optimized_results[test_name]['execution_time']:.2f}s")
                
            except Exception as e:
                self.optimized_results[test_name] = {
                    "execution_time": 0,
                    "success": False,
                    "output_size": 0,
                    "error": str(e)
                }
                logger.error(f"Optimized {test_name}: Error - {e}")
    
    def _generate_comparison_report(self):
        """Generate detailed comparison report."""
        report = {
            "test_summary": {
                "baseline_tests": len(self.baseline_results),
                "optimized_tests": len(self.optimized_results),
                "test_timestamp": time.time()
            },
            "performance_improvements": {},
            "success_rate_improvements": {},
            "overall_metrics": {}
        }
        
        # Calculate improvements for each test
        for test_name in self.baseline_results:
            if test_name in self.optimized_results:
                baseline = self.baseline_results[test_name]
                optimized = self.optimized_results[test_name]
                
                # Performance improvement
                if baseline["execution_time"] > 0:
                    improvement = (baseline["execution_time"] - optimized["execution_time"]) / baseline["execution_time"]
                    speedup = baseline["execution_time"] / optimized["execution_time"] if optimized["execution_time"] > 0 else float('inf')
                else:
                    improvement = 0
                    speedup = 1
                
                report["performance_improvements"][test_name] = {
                    "baseline_time": baseline["execution_time"],
                    "optimized_time": optimized["execution_time"],
                    "improvement_percent": improvement * 100,
                    "speedup_factor": speedup,
                    "time_saved": baseline["execution_time"] - optimized["execution_time"]
                }
                
                # Success rate improvement
                report["success_rate_improvements"][test_name] = {
                    "baseline_success": baseline["success"],
                    "optimized_success": optimized["success"],
                    "improvement": optimized["success"] and not baseline["success"]
                }
        
        # Calculate overall metrics
        baseline_times = [r["execution_time"] for r in self.baseline_results.values() if r["execution_time"] > 0]
        optimized_times = [r["execution_time"] for r in self.optimized_results.values() if r["execution_time"] > 0]
        
        baseline_successes = sum(1 for r in self.baseline_results.values() if r["success"])
        optimized_successes = sum(1 for r in self.optimized_results.values() if r["success"])
        
        if baseline_times and optimized_times:
            avg_baseline_time = sum(baseline_times) / len(baseline_times)
            avg_optimized_time = sum(optimized_times) / len(optimized_times)
            overall_speedup = avg_baseline_time / avg_optimized_time if avg_optimized_time > 0 else float('inf')
        else:
            avg_baseline_time = 0
            avg_optimized_time = 0
            overall_speedup = 1
        
        baseline_success_rate = baseline_successes / len(self.baseline_results) if self.baseline_results else 0
        optimized_success_rate = optimized_successes / len(self.optimized_results) if self.optimized_results else 0
        
        report["overall_metrics"] = {
            "avg_baseline_time": avg_baseline_time,
            "avg_optimized_time": avg_optimized_time,
            "overall_speedup": overall_speedup,
            "baseline_success_rate": baseline_success_rate,
            "optimized_success_rate": optimized_success_rate,
            "success_rate_improvement": optimized_success_rate - baseline_success_rate,
            "total_time_saved": sum(baseline_times) - sum(optimized_times),
            "performance_rating": self._calculate_performance_rating(report)
        }
        
        return report
    
    def _calculate_performance_rating(self, report):
        """Calculate overall performance rating (1-10)."""
        metrics = report["overall_metrics"]
        
        base_rating = 5
        
        # Adjust for speedup
        speedup = metrics.get("overall_speedup", 1)
        if speedup > 3:
            base_rating += 3
        elif speedup > 2:
            base_rating += 2
        elif speedup > 1.5:
            base_rating += 1
        elif speedup < 0.8:
            base_rating -= 2
        
        # Adjust for success rate
        success_improvement = metrics.get("success_rate_improvement", 0)
        if success_improvement > 0.3:
            base_rating += 2
        elif success_improvement > 0.1:
            base_rating += 1
        elif success_improvement < -0.1:
            base_rating -= 2
        
        return max(1, min(10, base_rating))

async def main():
    """Main test runner."""
    tester = PerformanceComparisonTest()
    
    try:
        report = await tester.run_comparison_test()
        
        # Print summary
        print("\\n" + "="*80)
        print("MSFConsole Performance Enhancement Results")
        print("="*80)
        
        overall = report["overall_metrics"]
        print(f"Overall Speedup: {overall['overall_speedup']:.2f}x")
        print(f"Baseline Success Rate: {overall['baseline_success_rate']:.1%}")
        print(f"Optimized Success Rate: {overall['optimized_success_rate']:.1%}")
        print(f"Success Rate Improvement: {overall['success_rate_improvement']:+.1%}")
        print(f"Total Time Saved: {overall['total_time_saved']:.2f}s")
        print(f"Performance Rating: {overall['performance_rating']}/10")
        
        print("\\nPer-Test Improvements:")
        for test_name, improvement in report["performance_improvements"].items():
            print(f"  {test_name}: {improvement['speedup_factor']:.2f}x speedup ({improvement['improvement_percent']:+.1f}%)")
        
        # Save detailed report
        report_file = f"performance_comparison_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\\nDetailed report saved to: {report_file}")
        
        return overall['performance_rating']
        
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        return 0

if __name__ == "__main__":
    rating = asyncio.run(main())
    exit(0 if rating >= 7 else 1)