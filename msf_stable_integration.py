#!/usr/bin/env python3

"""
MSFConsole Stable Integration
----------------------------
Reliability-focused MSFConsole integration with gradual performance enhancements.
Priority: Stability (95%+ success rate) > Performance gains.
"""

import asyncio
import logging
import time
import json
import subprocess
import os
import signal
import threading
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from pathlib import Path
import psutil
from enum import Enum
import queue

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationStatus(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    PARTIAL = "partial"

@dataclass
class OperationResult:
    status: OperationStatus
    data: Any
    execution_time: float
    error: Optional[str] = None
    warnings: List[str] = None

class MSFConsoleStableWrapper:
    """Stable, reliable MSFConsole wrapper with enhanced error handling."""
    
    def __init__(self):
        self.session_active = False
        self.initialization_status = "not_started"
        self.performance_stats = {
            "operations_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "total_execution_time": 0.0
        }
        self.config = self._load_stable_config()
        self.process_monitor = None
        
    def _load_stable_config(self) -> Dict[str, Any]:
        """Load stability-focused configuration."""
        return {
            "timeouts": {
                "initialization": 60.0,      # Conservative timeout
                "command_execution": 30.0,   # Generous timeout
                "payload_generation": 90.0,  # Extended for complex payloads
                "module_search": 20.0,       # Allow thorough search
                "cleanup": 10.0              # Process cleanup time
            },
            "retry_settings": {
                "max_retries": 3,
                "retry_delay": 2.0,
                "backoff_multiplier": 1.5
            },
            "stability_features": {
                "pre_validation": True,       # Validate before execution
                "post_validation": True,      # Validate results
                "graceful_degradation": True, # Continue with limited functionality
                "resource_monitoring": True,  # Monitor system resources
                "automatic_recovery": True    # Auto-recover from failures
            },
            "process_settings": {
                "nice_priority": 10,         # Lower priority to avoid system impact
                "memory_limit_mb": 1024,     # Memory limit for MSF processes
                "cpu_limit_percent": 50      # CPU usage limit
            }
        }
    
    async def initialize(self) -> OperationResult:
        """Initialize MSFConsole with comprehensive error handling."""
        start_time = time.time()
        self.initialization_status = "in_progress"
        
        try:
            logger.info("Initializing MSFConsole with stability focus...")
            
            # Pre-initialization checks
            if not await self._pre_initialization_checks():
                return OperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Pre-initialization checks failed"
                )
            
            # Progressive initialization with fallbacks
            initialization_attempts = [
                self._attempt_standard_initialization,
                self._attempt_minimal_initialization,
                self._attempt_offline_initialization
            ]
            
            for attempt_num, init_method in enumerate(initialization_attempts, 1):
                logger.info(f"Initialization attempt {attempt_num}/3...")
                
                try:
                    result = await asyncio.wait_for(
                        init_method(),
                        timeout=self.config["timeouts"]["initialization"]
                    )
                    
                    if result:
                        self.initialization_status = "completed"
                        self.session_active = True
                        logger.info(f"MSFConsole initialized successfully (attempt {attempt_num})")
                        
                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data={"initialization_method": init_method.__name__, "attempt": attempt_num},
                            execution_time=time.time() - start_time
                        )
                
                except asyncio.TimeoutError:
                    logger.warning(f"Initialization attempt {attempt_num} timed out")
                    continue
                except Exception as e:
                    logger.warning(f"Initialization attempt {attempt_num} failed: {e}")
                    continue
            
            # All initialization attempts failed
            self.initialization_status = "failed"
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="All initialization attempts failed"
            )
            
        except Exception as e:
            self.initialization_status = "error"
            logger.error(f"Critical initialization error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Critical error: {str(e)}"
            )
    
    async def _pre_initialization_checks(self) -> bool:
        """Perform pre-initialization system checks."""
        logger.debug("Performing pre-initialization checks...")
        
        checks = [
            ("MSFConsole binary available", self._check_msfconsole_binary),
            ("System resources adequate", self._check_system_resources),
            ("Required directories accessible", self._check_directories),
            ("Network connectivity", self._check_network_connectivity)
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                if await check_func():
                    logger.debug(f"✓ {check_name}")
                else:
                    logger.warning(f"✗ {check_name}")
                    all_passed = False
            except Exception as e:
                logger.warning(f"✗ {check_name}: {e}")
                all_passed = False
        
        return all_passed
    
    async def _check_msfconsole_binary(self) -> bool:
        """Check if msfconsole binary is available."""
        try:
            result = subprocess.run(
                ["which", "msfconsole"], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    async def _check_system_resources(self) -> bool:
        """Check if system has adequate resources."""
        try:
            memory = psutil.virtual_memory()
            cpu_count = psutil.cpu_count()
            
            # Require at least 2GB free memory and 2 CPU cores
            return memory.available > 2 * 1024 * 1024 * 1024 and cpu_count >= 2
        except:
            return False
    
    async def _check_directories(self) -> bool:
        """Check required directories are accessible."""
        try:
            # Check common MSF directories
            home_dir = Path.home()
            msf_dirs = [
                home_dir / ".msf4",
                Path("/usr/share/metasploit-framework"),
                Path("/opt/metasploit-framework")
            ]
            
            # At least one MSF directory should exist
            return any(path.exists() and path.is_dir() for path in msf_dirs)
        except:
            return False
    
    async def _check_network_connectivity(self) -> bool:
        """Check basic network connectivity."""
        try:
            # Simple ping test
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "3", "8.8.8.8"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return True  # Don't fail initialization for network issues
    
    async def _attempt_standard_initialization(self) -> bool:
        """Attempt standard MSFConsole initialization."""
        try:
            logger.debug("Attempting standard initialization...")
            
            # Test basic MSF functionality
            result = subprocess.run(
                ["msfconsole", "--version"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                # Test database connectivity
                db_result = subprocess.run(
                    ["msfconsole", "-q", "-x", "db_status; exit"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                return db_result.returncode == 0
            
            return False
            
        except subprocess.TimeoutExpired:
            logger.warning("Standard initialization timed out")
            return False
        except Exception as e:
            logger.warning(f"Standard initialization failed: {e}")
            return False
    
    async def _attempt_minimal_initialization(self) -> bool:
        """Attempt minimal MSFConsole initialization."""
        try:
            logger.debug("Attempting minimal initialization...")
            
            # Just verify msfconsole can run
            result = subprocess.run(
                ["msfconsole", "-h"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and "Usage:" in result.stdout
            
        except Exception as e:
            logger.warning(f"Minimal initialization failed: {e}")
            return False
    
    async def _attempt_offline_initialization(self) -> bool:
        """Attempt offline mode initialization."""
        try:
            logger.debug("Attempting offline initialization...")
            
            # Test msfvenom (doesn't require database)
            result = subprocess.run(
                ["msfvenom", "--list", "platforms"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0 and len(result.stdout) > 0
            
        except Exception as e:
            logger.warning(f"Offline initialization failed: {e}")
            return False
    
    async def execute_command(self, command: str, timeout: Optional[float] = None) -> OperationResult:
        """Execute MSFConsole command with comprehensive error handling."""
        if not self.session_active:
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=0,
                error="MSFConsole not initialized"
            )
        
        start_time = time.time()
        timeout = timeout or self.config["timeouts"]["command_execution"]
        
        # Update statistics
        self.performance_stats["operations_count"] += 1
        
        try:
            # Pre-execution validation
            if not self._validate_command(command):
                self.performance_stats["failure_count"] += 1
                return OperationResult(
                    status=OperationStatus.FAILURE,
                    data=None,
                    execution_time=time.time() - start_time,
                    error="Command validation failed"
                )
            
            # Execute with retry logic
            for attempt in range(self.config["retry_settings"]["max_retries"]):
                try:
                    logger.debug(f"Executing command (attempt {attempt + 1}): {command}")
                    
                    result = await self._execute_with_timeout(command, timeout)
                    
                    # Post-execution validation
                    if self._validate_result(result):
                        execution_time = time.time() - start_time
                        self.performance_stats["success_count"] += 1
                        self.performance_stats["total_execution_time"] += execution_time
                        
                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data=result,
                            execution_time=execution_time
                        )
                    else:
                        logger.warning(f"Result validation failed for: {command}")
                        
                except asyncio.TimeoutError:
                    logger.warning(f"Command timeout (attempt {attempt + 1}): {command}")
                    if attempt == self.config["retry_settings"]["max_retries"] - 1:
                        self.performance_stats["failure_count"] += 1
                        return OperationResult(
                            status=OperationStatus.TIMEOUT,
                            data=None,
                            execution_time=time.time() - start_time,
                            error=f"Command timed out after {timeout}s"
                        )
                
                # Wait before retry
                if attempt < self.config["retry_settings"]["max_retries"] - 1:
                    delay = self.config["retry_settings"]["retry_delay"] * (
                        self.config["retry_settings"]["backoff_multiplier"] ** attempt
                    )
                    await asyncio.sleep(delay)
            
            # All retries failed
            self.performance_stats["failure_count"] += 1
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="All retry attempts failed"
            )
            
        except Exception as e:
            self.performance_stats["failure_count"] += 1
            logger.error(f"Command execution error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Execution error: {str(e)}"
            )
    
    def _validate_command(self, command: str) -> bool:
        """Validate command before execution."""
        if not command or not command.strip():
            return False
        
        # Basic safety checks for system commands only
        dangerous_commands = ["rm -rf", "del /", "format c:", "shutdown", "reboot", "killall"]
        command_lower = command.lower()
        
        # Only block exact dangerous system commands, not MSF search terms
        if any(dangerous in command_lower for dangerous in dangerous_commands):
            logger.warning(f"Potentially dangerous command blocked: {command}")
            return False
        
        return True
    
    def _validate_result(self, result: Dict[str, Any]) -> bool:
        """Validate command execution result."""
        if not isinstance(result, dict):
            return False
        
        # Check for critical errors
        if result.get("returncode", 0) != 0:
            stderr = result.get("stderr", "")
            if "fatal" in stderr.lower() or "critical" in stderr.lower():
                return False
        
        return True
    
    async def _execute_with_timeout(self, command: str, timeout: float) -> Dict[str, Any]:
        """Execute command with timeout and resource monitoring."""
        full_command = ["msfconsole", "-q", "-x", f"{command}; exit"]
        
        # Set up resource limits
        env = os.environ.copy()
        env.update({
            "MSF_DATABASE_CONFIG": "/dev/null",  # Reduce database overhead
            "LANG": "en_US.UTF-8"
        })
        
        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return {
                "stdout": stdout.decode('utf-8', errors='replace'),
                "stderr": stderr.decode('utf-8', errors='replace'),
                "returncode": process.returncode
            }
            
        except asyncio.TimeoutError:
            # Clean process termination
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=5)
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
            raise
    
    async def generate_payload(self, payload: str, options: Dict[str, str], 
                             output_format: str = "raw", encoder: Optional[str] = None) -> OperationResult:
        """Generate payload with enhanced stability."""
        start_time = time.time()
        timeout = self.config["timeouts"]["payload_generation"]
        
        try:
            # Build msfvenom command
            cmd = ["msfvenom", "-p", payload]
            
            # Add options
            for key, value in options.items():
                cmd.extend([f"{key}={value}"])
            
            # Add format
            cmd.extend(["-f", output_format])
            
            # Add encoder if specified
            if encoder:
                cmd.extend(["-e", encoder])
            
            logger.debug(f"Generating payload: {' '.join(cmd)}")
            
            # Execute with multiple fallback methods
            for attempt in range(3):
                try:
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    
                    if process.returncode == 0 and stdout:
                        return OperationResult(
                            status=OperationStatus.SUCCESS,
                            data={
                                "payload_data": stdout.decode('utf-8', errors='replace'),
                                "size_bytes": len(stdout),
                                "format": output_format,
                                "encoder": encoder
                            },
                            execution_time=time.time() - start_time
                        )
                    else:
                        logger.warning(f"Payload generation attempt {attempt + 1} failed")
                        if attempt < 2:  # Wait before retry
                            await asyncio.sleep(2)
                
                except asyncio.TimeoutError:
                    logger.warning(f"Payload generation timeout (attempt {attempt + 1})")
                    if attempt < 2:
                        await asyncio.sleep(2)
            
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error="Payload generation failed after 3 attempts"
            )
            
        except Exception as e:
            logger.error(f"Payload generation error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Generation error: {str(e)}"
            )
    
    async def search_modules(self, query: str, limit: int = 25, page: int = 1) -> OperationResult:
        """Search modules with pagination support and token limit management."""
        start_time = time.time()
        
        try:
            # Apply smart defaults to prevent token overflow
            if limit > 50:  # Reduce default limit to prevent token overflow
                limit = 50
                logger.info(f"Reduced limit to {limit} to prevent token overflow")
            
            search_command = f"search {query}"
            result = await self.execute_command(search_command, 
                                               timeout=self.config["timeouts"]["module_search"])
            
            if result.status == OperationStatus.SUCCESS:
                # Parse all search results first
                all_modules = self._parse_search_output_full(result.data["stdout"])
                total_count = len(all_modules)
                
                # Apply pagination
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                paginated_modules = all_modules[start_idx:end_idx]
                
                total_pages = (total_count + limit - 1) // limit  # Ceiling division
                
                # Estimate token count and reduce results if needed
                estimated_tokens = self._estimate_response_tokens(paginated_modules)
                if estimated_tokens > 20000:  # Leave buffer under 25k limit
                    # Reduce results to fit token limit
                    reduced_limit = max(1, len(paginated_modules) * 20000 // estimated_tokens)
                    paginated_modules = paginated_modules[:reduced_limit]
                    logger.warning(f"Reduced results from {limit} to {reduced_limit} due to token limit")
                
                return OperationResult(
                    status=OperationStatus.SUCCESS,
                    data={
                        "query": query,
                        "modules": paginated_modules,
                        "pagination": {
                            "current_page": page,
                            "total_pages": total_pages,
                            "page_size": limit,
                            "total_count": total_count,
                            "has_next": page < total_pages,
                            "has_previous": page > 1,
                            "token_limit_applied": estimated_tokens > 20000
                        },
                        "search_tips": {
                            "narrow_search": "Use more specific terms to reduce results",
                            "pagination": f"Use page parameter (1-{total_pages}) to navigate",
                            "examples": [
                                "exploit platform:windows type:local",
                                "auxiliary scanner", 
                                "post gather platform:linux"
                            ]
                        }
                    },
                    execution_time=time.time() - start_time
                )
            else:
                return result  # Pass through the error
            
        except Exception as e:
            logger.error(f"Module search error: {e}")
            return OperationResult(
                status=OperationStatus.FAILURE,
                data=None,
                execution_time=time.time() - start_time,
                error=f"Search error: {str(e)}"
            )
    
    def _estimate_response_tokens(self, modules: List[Dict[str, Any]]) -> int:
        """Estimate token count for search response."""
        if not modules:
            return 0
        
        # Rough estimation: ~4 chars per token, each module ~200 chars average
        chars_per_module = 200
        total_chars = len(modules) * chars_per_module
        return total_chars // 4
    
    def _parse_search_output_full(self, output: str) -> List[Dict[str, Any]]:
        """Parse all module search output without limits."""
        modules = []
        lines = output.split('\\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('=') or line.startswith('[') or line.startswith('Matching'):
                continue
            
            # Enhanced parsing for MSF output format
            parts = line.split()
            if len(parts) >= 2:
                modules.append({
                    "name": parts[0],
                    "description": " ".join(parts[1:]),
                    "type": self._extract_module_type(parts[0])
                })
        
        return modules
    
    def _parse_search_output(self, output: str, limit: int) -> List[Dict[str, Any]]:
        """Legacy method with limit for backward compatibility."""
        all_modules = self._parse_search_output_full(output)
        return all_modules[:limit]
    
    def _extract_module_type(self, module_name: str) -> str:
        """Extract module type from name."""
        if "/" not in module_name:
            return "unknown"
        
        type_part = module_name.split("/")[0]
        return type_part if type_part in ["exploit", "auxiliary", "post", "payload", "encoder", "nop"] else "unknown"
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information."""
        success_rate = 0
        if self.performance_stats["operations_count"] > 0:
            success_rate = self.performance_stats["success_count"] / self.performance_stats["operations_count"]
        
        avg_execution_time = 0
        if self.performance_stats["success_count"] > 0:
            avg_execution_time = self.performance_stats["total_execution_time"] / self.performance_stats["success_count"]
        
        return {
            "initialization_status": self.initialization_status,
            "session_active": self.session_active,
            "performance_stats": {
                **self.performance_stats,
                "success_rate": success_rate,
                "avg_execution_time": avg_execution_time
            },
            "system_resources": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "process_memory_mb": psutil.Process().memory_info().rss / 1024 / 1024
            },
            "stability_rating": self._calculate_stability_rating()
        }
    
    def _calculate_stability_rating(self) -> int:
        """Calculate stability rating (1-10)."""
        if self.performance_stats["operations_count"] == 0:
            return 10 if self.initialization_status == "completed" else 5
        
        success_rate = self.performance_stats["success_count"] / self.performance_stats["operations_count"]
        
        if success_rate >= 0.95:
            return 10
        elif success_rate >= 0.90:
            return 9
        elif success_rate >= 0.80:
            return 8
        elif success_rate >= 0.70:
            return 7
        elif success_rate >= 0.60:
            return 6
        elif success_rate >= 0.50:
            return 5
        else:
            return max(1, int(success_rate * 10))
    
    async def cleanup(self):
        """Clean up resources and terminate processes."""
        logger.info("Cleaning up MSFConsole integration...")
        
        try:
            if self.process_monitor:
                self.process_monitor.stop()
            
            self.session_active = False
            self.initialization_status = "cleanup"
            
            # Final status report
            status = self.get_status()
            logger.info(f"Final stability rating: {status['stability_rating']}/10")
            logger.info(f"Total operations: {status['performance_stats']['operations_count']}")
            logger.info(f"Success rate: {status['performance_stats']['success_rate']:.1%}")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")

# Factory function
def create_stable_msf_console() -> MSFConsoleStableWrapper:
    """Create a stable MSFConsole wrapper instance."""
    return MSFConsoleStableWrapper()

# Example usage and testing
if __name__ == "__main__":
    async def main():
        msf = create_stable_msf_console()
        
        try:
            # Initialize
            init_result = await msf.initialize()
            print(f"Initialization: {init_result.status.value}")
            
            if init_result.status == OperationStatus.SUCCESS:
                # Test basic commands
                commands = ["version", "help", "db_status"]
                
                for cmd in commands:
                    result = await msf.execute_command(cmd)
                    print(f"Command '{cmd}': {result.status.value} ({result.execution_time:.2f}s)")
                
                # Test payload generation
                payload_result = await msf.generate_payload(
                    "windows/meterpreter/reverse_tcp",
                    {"LHOST": "127.0.0.1", "LPORT": "4444"}
                )
                print(f"Payload generation: {payload_result.status.value}")
                
                # Test module search
                search_result = await msf.search_modules("exploit platform:windows")
                print(f"Module search: {search_result.status.value}")
                
                # Final status
                status = msf.get_status()
                print(f"\\nFinal Status:")
                print(f"Stability Rating: {status['stability_rating']}/10")
                print(f"Success Rate: {status['performance_stats']['success_rate']:.1%}")
            
        finally:
            await msf.cleanup()
    
    asyncio.run(main())