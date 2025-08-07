#!/usr/bin/env python3

"""
MSFConsole Performance Enhancement Implementation
-----------------------------------------------
Advanced performance optimizations based on comprehensive test results.
Target: Improve 28.9% success rate to 90%+ with 5-10x performance gains.
"""

import asyncio
import logging
import time
import json
import threading
import concurrent.futures
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import subprocess
import psutil
import os
import signal
from collections import defaultdict, deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    operation: str
    start_time: float
    end_time: float
    success: bool
    memory_usage: float
    error: Optional[str] = None

class PerformanceMonitor:
    """Real-time performance monitoring and optimization."""
    
    def __init__(self):
        self.metrics = deque(maxlen=1000)
        self.alert_thresholds = {
            'memory_mb': 500,
            'execution_time': 30.0,
            'success_rate_min': 0.8
        }
        self.running = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start background performance monitoring."""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        logger.info("Performance monitoring stopped")
    
    def record_metric(self, operation: str, start_time: float, success: bool, error: Optional[str] = None):
        """Record a performance metric."""
        end_time = time.time()
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        
        metric = PerformanceMetrics(
            operation=operation,
            start_time=start_time,
            end_time=end_time,
            success=success,
            memory_usage=memory_usage,
            error=error
        )
        
        self.metrics.append(metric)
        self._check_alerts(metric)
    
    def _monitor_loop(self):
        """Background monitoring loop."""
        while self.running:
            try:
                # Check system resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory_percent = psutil.virtual_memory().percent
                
                if cpu_percent > 90:
                    logger.warning(f"High CPU usage: {cpu_percent}%")
                if memory_percent > 85:
                    logger.warning(f"High memory usage: {memory_percent}%")
                
                time.sleep(5)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
    
    def _check_alerts(self, metric: PerformanceMetrics):
        """Check for performance alerts."""
        execution_time = metric.end_time - metric.start_time
        
        if execution_time > self.alert_thresholds['execution_time']:
            logger.warning(f"Slow operation: {metric.operation} took {execution_time:.2f}s")
        
        if metric.memory_usage > self.alert_thresholds['memory_mb']:
            logger.warning(f"High memory usage: {metric.memory_usage:.1f}MB in {metric.operation}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        if not self.metrics:
            return {"error": "No metrics available"}
        
        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]
        
        execution_times = [m.end_time - m.start_time for m in self.metrics]
        memory_usage = [m.memory_usage for m in self.metrics]
        
        return {
            "total_operations": len(self.metrics),
            "successful_operations": len(successful),
            "failed_operations": len(failed),
            "success_rate": len(successful) / len(self.metrics) if self.metrics else 0,
            "avg_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
            "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            "slowest_operation": max(execution_times) if execution_times else 0,
            "peak_memory": max(memory_usage) if memory_usage else 0
        }

class AsyncProcessPool:
    """High-performance async process pool for MSF operations."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.process_cache = {}
        self.lock = asyncio.Lock()
    
    async def execute_command(self, command: List[str], timeout: float = 30.0) -> Tuple[str, str, int]:
        """Execute command with optimized process handling."""
        loop = asyncio.get_event_loop()
        
        try:
            # Execute in thread pool to avoid blocking
            future = loop.run_in_executor(
                self.executor,
                self._run_subprocess,
                command,
                timeout
            )
            
            stdout, stderr, returncode = await asyncio.wait_for(future, timeout=timeout + 5)
            return stdout, stderr, returncode
            
        except asyncio.TimeoutError:
            logger.error(f"Command timeout: {' '.join(command)}")
            return "", f"Command timed out after {timeout}s", -1
        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return "", f"Execution error: {str(e)}", -1
    
    def _run_subprocess(self, command: List[str], timeout: float) -> Tuple[str, str, int]:
        """Run subprocess with optimized settings."""
        try:
            # Optimized subprocess settings
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=8192,  # Larger buffer for better performance
                preexec_fn=os.setsid if os.name != 'nt' else None  # Process group for clean termination
            )
            
            stdout, stderr = process.communicate(timeout=timeout)
            return stdout, stderr, process.returncode
            
        except subprocess.TimeoutExpired:
            # Clean process termination
            if os.name != 'nt':
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            else:
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                else:
                    process.kill()
            return "", f"Process timed out after {timeout}s", -1
        except Exception as e:
            return "", f"Subprocess error: {str(e)}", -1
    
    def close(self):
        """Close the process pool."""
        self.executor.shutdown(wait=True)

class MSFConsoleOptimizer:
    """Advanced MSFConsole performance optimizer."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
        self.process_pool = AsyncProcessPool(max_workers=6)
        self.command_cache = {}
        self.performance_config = self._load_performance_config()
        self.session_pool = {}
        self.connection_pool = {}
        
    def _load_performance_config(self) -> Dict[str, Any]:
        """Load performance optimization configuration."""
        return {
            "msfconsole_args": [
                "-q",  # Quiet mode
                "-x", "db_status; workspace -a default",  # Auto-initialize workspace
            ],
            "environment_vars": {
                "MSF_DATABASE_CONFIG": "/dev/null",  # Disable database logging
                "RUBY_GC_HEAP_INIT_SLOTS": "100000",  # Pre-allocate Ruby objects
                "RUBY_GC_HEAP_FREE_SLOTS": "10000",
                "RUBY_GC_HEAP_GROWTH_FACTOR": "1.1",
                "RUBY_GC_HEAP_GROWTH_MAX_SLOTS": "10000",
                "LANG": "en_US.UTF-8",
                "LC_ALL": "en_US.UTF-8"
            },
            "timeout_settings": {
                "initialization": 30.0,
                "command_execution": 15.0,
                "payload_generation": 45.0,
                "module_search": 10.0
            },
            "concurrency_limits": {
                "max_concurrent_commands": 4,
                "max_concurrent_payloads": 2,
                "max_concurrent_searches": 3
            }
        }
    
    async def start_optimization(self):
        """Start performance optimization systems."""
        logger.info("Starting MSFConsole performance optimization...")
        self.monitor.start_monitoring()
        
        # Pre-warm critical components
        await self._prewarm_system()
        
        logger.info("Performance optimization active")
    
    async def stop_optimization(self):
        """Stop optimization systems."""
        logger.info("Stopping performance optimization...")
        self.monitor.stop_monitoring()
        self.process_pool.close()
        logger.info("Performance optimization stopped")
    
    async def _prewarm_system(self):
        """Pre-warm system components for faster startup."""
        logger.info("Pre-warming system components...")
        
        prewarm_tasks = [
            self._prewarm_msfconsole(),
            self._prewarm_database(),
            self._prewarm_module_cache()
        ]
        
        await asyncio.gather(*prewarm_tasks, return_exceptions=True)
        logger.info("System pre-warming completed")
    
    async def _prewarm_msfconsole(self):
        """Pre-warm MSFConsole for faster subsequent operations."""
        try:
            start_time = time.time()
            
            # Quick version check to initialize MSF
            stdout, stderr, returncode = await self.process_pool.execute_command(
                ["msfconsole", "--version"],
                timeout=10.0
            )
            
            success = returncode == 0
            self.monitor.record_metric("prewarm_msfconsole", start_time, success, stderr if not success else None)
            
            if success:
                logger.info("MSFConsole pre-warming successful")
            else:
                logger.warning(f"MSFConsole pre-warming failed: {stderr}")
                
        except Exception as e:
            logger.error(f"MSFConsole pre-warming error: {e}")
    
    async def _prewarm_database(self):
        """Pre-warm database connections."""
        try:
            start_time = time.time()
            
            # Initialize database connection
            stdout, stderr, returncode = await self.process_pool.execute_command(
                ["msfconsole", "-q", "-x", "db_status; exit"],
                timeout=15.0
            )
            
            success = returncode == 0 and "Connected" in stdout
            self.monitor.record_metric("prewarm_database", start_time, success, stderr if not success else None)
            
        except Exception as e:
            logger.error(f"Database pre-warming error: {e}")
    
    async def _prewarm_module_cache(self):
        """Pre-warm module cache for faster searches."""
        try:
            start_time = time.time()
            
            # Quick module search to populate cache
            stdout, stderr, returncode = await self.process_pool.execute_command(
                ["msfconsole", "-q", "-x", "search type:exploit platform:windows; exit"],
                timeout=20.0
            )
            
            success = returncode == 0
            self.monitor.record_metric("prewarm_module_cache", start_time, success, stderr if not success else None)
            
        except Exception as e:
            logger.error(f"Module cache pre-warming error: {e}")
    
    async def optimized_command_execution(self, command: str, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Execute MSFConsole command with optimizations."""
        if timeout is None:
            timeout = self.performance_config["timeout_settings"]["command_execution"]
        
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"cmd_{hash(command)}"
            if cache_key in self.command_cache:
                logger.debug(f"Using cached result for: {command}")
                self.monitor.record_metric("command_execution_cached", start_time, True)
                return self.command_cache[cache_key]
            
            # Prepare optimized command
            full_command = [
                "msfconsole",
                *self.performance_config["msfconsole_args"],
                "-x", f"{command}; exit"
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env.update(self.performance_config["environment_vars"])
            
            # Execute with process pool
            stdout, stderr, returncode = await self.process_pool.execute_command(
                full_command,
                timeout=timeout
            )
            
            success = returncode == 0
            result = {
                "success": success,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "execution_time": time.time() - start_time
            }
            
            # Cache successful results for non-stateful commands
            if success and self._is_cacheable_command(command):
                self.command_cache[cache_key] = result
            
            self.monitor.record_metric("command_execution", start_time, success, stderr if not success else None)
            return result
            
        except Exception as e:
            error_msg = f"Command execution failed: {str(e)}"
            logger.error(error_msg)
            self.monitor.record_metric("command_execution", start_time, False, error_msg)
            
            return {
                "success": False,
                "stdout": "",
                "stderr": error_msg,
                "returncode": -1,
                "execution_time": time.time() - start_time
            }
    
    def _is_cacheable_command(self, command: str) -> bool:
        """Determine if command results can be cached."""
        non_cacheable = ["workspace", "sessions", "jobs", "db_status", "exit", "quit"]
        return not any(keyword in command.lower() for keyword in non_cacheable)
    
    async def optimized_payload_generation(self, payload: str, options: Dict[str, str], 
                                         output_format: str = "raw", encoder: Optional[str] = None) -> Dict[str, Any]:
        """Generate payload with performance optimizations."""
        timeout = self.performance_config["timeout_settings"]["payload_generation"]
        start_time = time.time()
        
        try:
            # Build msfvenom command with optimizations
            cmd = ["msfvenom", "-p", payload]
            
            # Add options
            for key, value in options.items():
                cmd.extend([key + "=" + str(value)])
            
            # Add format and encoder
            cmd.extend(["-f", output_format])
            if encoder:
                cmd.extend(["-e", encoder])
            
            # Add performance flags
            cmd.extend(["--platform", "auto", "--arch", "auto"])
            
            # Execute with optimizations
            stdout, stderr, returncode = await self.process_pool.execute_command(cmd, timeout=timeout)
            
            success = returncode == 0 and len(stdout) > 0
            result = {
                "success": success,
                "payload_data": stdout if success else "",
                "error": stderr if not success else "",
                "size_bytes": len(stdout) if success else 0,
                "generation_time": time.time() - start_time
            }
            
            self.monitor.record_metric("payload_generation", start_time, success, stderr if not success else None)
            return result
            
        except Exception as e:
            error_msg = f"Payload generation failed: {str(e)}"
            logger.error(error_msg)
            self.monitor.record_metric("payload_generation", start_time, False, error_msg)
            
            return {
                "success": False,
                "payload_data": "",
                "error": error_msg,
                "size_bytes": 0,
                "generation_time": time.time() - start_time
            }
    
    async def optimized_module_search(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search modules with performance optimizations."""
        timeout = self.performance_config["timeout_settings"]["module_search"]
        start_time = time.time()
        
        try:
            # Optimize search query
            optimized_query = self._optimize_search_query(query)
            search_command = f"search {optimized_query}"
            
            result = await self.optimized_command_execution(search_command, timeout)
            
            if result["success"]:
                # Parse search results
                modules = self._parse_search_results(result["stdout"], limit)
                result.update({
                    "modules": modules,
                    "module_count": len(modules),
                    "search_time": time.time() - start_time
                })
            
            return result
            
        except Exception as e:
            error_msg = f"Module search failed: {str(e)}"
            logger.error(error_msg)
            self.monitor.record_metric("module_search", start_time, False, error_msg)
            
            return {
                "success": False,
                "modules": [],
                "module_count": 0,
                "error": error_msg,
                "search_time": time.time() - start_time
            }
    
    def _optimize_search_query(self, query: str) -> str:
        """Optimize search query for better performance."""
        # Add common optimizations
        if not any(prefix in query for prefix in ["type:", "platform:", "name:"]):
            # Add basic filters to narrow search
            if "windows" in query.lower():
                query += " platform:windows"
            elif "linux" in query.lower():
                query += " platform:linux"
        
        return query
    
    def _parse_search_results(self, output: str, limit: int) -> List[Dict[str, Any]]:
        """Parse module search results efficiently."""
        modules = []
        lines = output.split('\n')
        
        for line in lines:
            if len(modules) >= limit:
                break
                
            # Simple parsing - can be enhanced based on actual MSF output format
            if line.strip() and not line.startswith('=') and not line.startswith('['):
                parts = line.split()
                if len(parts) >= 2:
                    modules.append({
                        "name": parts[0] if parts else "",
                        "description": " ".join(parts[1:]) if len(parts) > 1 else "",
                        "type": self._extract_module_type(parts[0]) if parts else "unknown"
                    })
        
        return modules
    
    def _extract_module_type(self, module_name: str) -> str:
        """Extract module type from module name."""
        if module_name.startswith("exploit/"):
            return "exploit"
        elif module_name.startswith("auxiliary/"):
            return "auxiliary"
        elif module_name.startswith("post/"):
            return "post"
        elif module_name.startswith("payload/"):
            return "payload"
        else:
            return "unknown"
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report."""
        performance_summary = self.monitor.get_performance_summary()
        
        return {
            "optimization_status": "active",
            "performance_summary": performance_summary,
            "cache_stats": {
                "command_cache_size": len(self.command_cache),
                "session_pool_size": len(self.session_pool),
                "connection_pool_size": len(self.connection_pool)
            },
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "process_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
            },
            "configuration": self.performance_config,
            "recommendations": self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []
        performance = self.monitor.get_performance_summary()
        
        if performance.get("success_rate", 0) < 0.9:
            recommendations.append("Consider increasing timeout values for better reliability")
        
        if performance.get("avg_execution_time", 0) > 10:
            recommendations.append("Enable more aggressive caching for frequently used commands")
        
        if performance.get("peak_memory", 0) > 1000:
            recommendations.append("Consider implementing memory cleanup routines")
        
        system_memory = psutil.virtual_memory().percent
        if system_memory > 80:
            recommendations.append("System memory usage is high - consider reducing concurrent operations")
        
        if not recommendations:
            recommendations.append("System is performing optimally - consider stress testing with higher loads")
        
        return recommendations

# Factory function for easy integration
def create_msf_optimizer() -> MSFConsoleOptimizer:
    """Create and configure an MSFConsole optimizer."""
    return MSFConsoleOptimizer()

if __name__ == "__main__":
    async def main():
        optimizer = create_msf_optimizer()
        await optimizer.start_optimization()
        
        try:
            # Demo optimization
            result = await optimizer.optimized_command_execution("version")
            print("Command result:", json.dumps(result, indent=2))
            
            # Generate report
            report = optimizer.get_optimization_report()
            print("\\nOptimization Report:", json.dumps(report, indent=2))
            
        finally:
            await optimizer.stop_optimization()
    
    asyncio.run(main())