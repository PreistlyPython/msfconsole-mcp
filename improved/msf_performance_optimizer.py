#!/usr/bin/env python3

"""
MSFConsole Performance Optimizer
-------------------------------
Addresses MSFConsole MCP performance issues including:
- Framework version updates and maintenance
- Initialization delay optimization
- Output parsing improvements
- Timeout management
"""

import asyncio
import logging
import subprocess
import os
import json
import re
import time
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

class MSFPerformanceOptimizer:
    """Comprehensive performance optimization for MSFConsole MCP."""
    
    def __init__(self):
        self.msf_path = self._find_executable("msfconsole")
        self.msfvenom_path = self._find_executable("msfvenom")
        self.framework_info = {}
        self.optimization_applied = False
        self.parsing_patterns = {}
        self.performance_cache = {}
        
    async def initialize(self) -> Dict[str, Any]:
        """Initialize performance optimizer with comprehensive checks."""
        logger.info("Initializing MSF Performance Optimizer...")
        
        results = {
            "framework_check": await self._check_framework_status(),
            "optimization_applied": await self._apply_performance_optimizations(),
            "parsing_patterns_loaded": await self._load_parsing_patterns(),
            "cache_initialized": await self._initialize_performance_cache()
        }
        
        self.optimization_applied = all(results.values())
        logger.info(f"MSF Performance Optimizer initialized: {results}")
        return results
    
    async def _check_framework_status(self) -> bool:
        """Check framework status and suggest updates."""
        try:
            if not self.msfvenom_path:
                logger.error("msfvenom not found")
                return False
            
            # Get framework version
            process = await asyncio.create_subprocess_exec(
                self.msfvenom_path, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version_output = stdout.decode('utf-8', errors='ignore')
                version_match = re.search(r"(\\d+\\.\\d+\\.\\d+)", version_output)
                
                if version_match:
                    version = version_match.group(1)
                    self.framework_info = {
                        "version": version,
                        "needs_update": self._version_needs_update(version),
                        "last_checked": time.time()
                    }
                    
                    if self.framework_info["needs_update"]:
                        logger.warning(f"Framework version {version} is outdated. Update recommended.")
                        await self._suggest_framework_update()
                    else:
                        logger.info(f"Framework version {version} is current")
                    
                    return True
            else:
                logger.error(f"Failed to check framework version: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Framework status check failed: {e}")
            return False
    
    async def _apply_performance_optimizations(self) -> bool:
        """Apply various performance optimizations."""
        try:
            optimizations = []
            
            # 1. Environment optimizations
            env_opts = await self._optimize_environment()
            optimizations.append(("environment", env_opts))
            
            # 2. Database optimizations
            db_opts = await self._optimize_database_settings()
            optimizations.append(("database", db_opts))
            
            # 3. Memory optimizations
            mem_opts = await self._optimize_memory_usage()
            optimizations.append(("memory", mem_opts))
            
            # 4. Network optimizations
            net_opts = await self._optimize_network_settings()
            optimizations.append(("network", net_opts))
            
            success_count = sum(1 for _, success in optimizations if success)
            logger.info(f"Applied {success_count}/{len(optimizations)} performance optimizations")
            
            return success_count >= len(optimizations) // 2  # At least half successful
            
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            return False
    
    async def _optimize_environment(self) -> bool:
        """Optimize environment variables for better performance."""
        try:
            optimizations = {
                # Reduce startup time
                'MSF_DATABASE_CONFIG': '/dev/null',  # Skip database config loading
                'MSF_WS_DATA_SERVICE_URL': '',       # Disable web service
                'METASPLOIT_FRAMEWORK_DISABLE_BUNDLER': '1',  # Skip bundler
                
                # Memory optimizations
                'RUBY_GC_HEAP_INIT_SLOTS': '100000',
                'RUBY_GC_HEAP_FREE_SLOTS': '100000',
                'RUBY_GC_MALLOC_LIMIT': '90000000',
                
                # Encoding fixes
                'LANG': 'en_US.UTF-8',
                'LC_ALL': 'en_US.UTF-8',
                'PYTHONIOENCODING': 'utf-8',
                
                # Performance tuning
                'MSF_THREAD_POOL_SIZE': '10',
                'MSF_MODULE_SEARCH_CACHE': '1',
            }
            
            for key, value in optimizations.items():
                os.environ[key] = value
            
            logger.info("Environment optimizations applied")
            return True
            
        except Exception as e:
            logger.error(f"Environment optimization failed: {e}")
            return False
    
    async def _optimize_database_settings(self) -> bool:
        """Optimize database settings for faster operations."""
        try:
            # Create optimized database configuration
            db_config = {
                "production": {
                    "adapter": "postgresql",
                    "database": "msf_production",
                    "username": "msf",
                    "password": "msf",
                    "host": "127.0.0.1",
                    "port": 5432,
                    "pool": 75,
                    "timeout": 5,
                    # Performance optimizations
                    "prepared_statements": False,
                    "advisory_locks": False,
                    "statement_timeout": "30s",
                    "idle_timeout": "60s"
                }
            }
            
            # Write optimized config if we can
            config_path = os.path.expanduser("~/.msf4/database.yml")
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            
            # Only update if we can write
            if os.access(os.path.dirname(config_path), os.W_OK):
                import yaml
                with open(config_path, 'w') as f:
                    yaml.dump(db_config, f)
                logger.info("Database configuration optimized")
            else:
                logger.info("Database optimization skipped (no write access)")
            
            return True
            
        except ImportError:
            logger.warning("PyYAML not available, skipping database config optimization")
            return True  # Not critical
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            return False
    
    async def _optimize_memory_usage(self) -> bool:
        """Optimize memory usage patterns."""
        try:
            # Set Ruby memory optimizations
            ruby_opts = [
                "--jit",                    # Enable JIT compilation
                "--jit-max-cache=10000",   # Increase JIT cache
                "--gc-compact",            # Enable GC compaction
            ]
            
            os.environ['RUBYOPT'] = ' '.join(ruby_opts)
            
            # Initialize performance cache with limits
            self.performance_cache = {
                "max_size": 1000,
                "ttl": 3600,  # 1 hour
                "data": {},
                "access_times": {}
            }
            
            logger.info("Memory optimizations applied")
            return True
            
        except Exception as e:
            logger.error(f"Memory optimization failed: {e}")
            return False
    
    async def _optimize_network_settings(self) -> bool:
        """Optimize network-related settings."""
        try:
            # Network timeout optimizations
            network_opts = {
                'MSF_CONNECT_TIMEOUT': '10',
                'MSF_READ_TIMEOUT': '30',
                'MSF_SSL_VERIFY': '0',  # Disable SSL verification for speed
                'MSF_HTTP_USER_AGENT': 'Mozilla/5.0 (compatible; MSF)'
            }
            
            for key, value in network_opts.items():
                os.environ[key] = value
            
            logger.info("Network optimizations applied")
            return True
            
        except Exception as e:
            logger.error(f"Network optimization failed: {e}")
            return False
    
    async def _load_parsing_patterns(self) -> bool:
        """Load and optimize output parsing patterns."""
        try:
            # Enhanced parsing patterns for better output handling
            self.parsing_patterns = {
                "module_search": {
                    "pattern": r"\\s*#\\s*(\\d+)\\s+(\\S+)\\s+(.+?)\\s+(\\d{4}-\\d{2}-\\d{2})\\s+(.+)",
                    "groups": ["number", "rank", "name", "date", "description"],
                    "cleanup": lambda x: x.strip()
                },
                "payload_generation": {
                    "pattern": r"Payload size: (\\d+) bytes.*?\\n(.+?)\\nmsf",
                    "groups": ["size", "payload"],
                    "multiline": True
                },
                "module_info": {
                    "pattern": r"Name:\\s*(.+?)\\n.*?Description:\\s*(.+?)\\n",
                    "groups": ["name", "description"],
                    "multiline": True
                },
                "options_table": {
                    "pattern": r"\\s*(\\w+)\\s+(\\w+)\\s+(\\w+)\\s+(.+?)\\s+(.+)",
                    "groups": ["name", "current", "required", "description", "type"],
                    "cleanup": lambda x: x.strip()
                },
                "session_list": {
                    "pattern": r"\\s*(\\d+)\\s+(\\w+)\\s+(\\S+)\\s+(\\S+)\\s+(.+)",
                    "groups": ["id", "type", "info", "tunnel", "via"],
                    "cleanup": lambda x: x.strip()
                }
            }
            
            logger.info(f"Loaded {len(self.parsing_patterns)} parsing patterns")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load parsing patterns: {e}")
            return False
    
    async def _initialize_performance_cache(self) -> bool:
        """Initialize performance monitoring and caching."""
        try:
            self.performance_cache = {
                "command_times": {},
                "cache_hits": 0,
                "cache_misses": 0,
                "total_commands": 0,
                "avg_response_time": 0
            }
            
            logger.info("Performance cache initialized")
            return True
            
        except Exception as e:
            logger.error(f"Performance cache initialization failed: {e}")
            return False
    
    def parse_output_enhanced(self, output: str, output_type: str) -> Dict[str, Any]:
        """Enhanced output parsing with optimized patterns."""
        try:
            if output_type not in self.parsing_patterns:
                return {"raw_output": output, "parsed": False}
            
            pattern_config = self.parsing_patterns[output_type]
            pattern = pattern_config["pattern"]
            groups = pattern_config["groups"]
            
            flags = re.MULTILINE
            if pattern_config.get("multiline"):
                flags |= re.DOTALL
            
            matches = re.findall(pattern, output, flags)
            
            if not matches:
                return {"raw_output": output, "parsed": False, "error": "No matches found"}
            
            parsed_data = []
            for match in matches:
                if isinstance(match, tuple):
                    item = {}
                    for i, group_name in enumerate(groups):
                        if i < len(match):
                            value = match[i]
                            if pattern_config.get("cleanup"):
                                value = pattern_config["cleanup"](value)
                            item[group_name] = value
                    parsed_data.append(item)
                else:
                    # Single match
                    parsed_data.append({groups[0]: match})
            
            return {
                "parsed": True,
                "data": parsed_data,
                "count": len(parsed_data),
                "type": output_type
            }
            
        except Exception as e:
            logger.error(f"Output parsing failed: {e}")
            return {"raw_output": output, "parsed": False, "error": str(e)}
    
    async def execute_with_optimization(self, command: str, msf_instance, timeout: int = 60) -> Dict[str, Any]:
        """Execute command with performance optimizations and monitoring."""
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"{command}:{hash(str(sorted(os.environ.items())))}"
            if cache_key in self.performance_cache.get("data", {}):
                cache_entry = self.performance_cache["data"][cache_key]
                if time.time() - cache_entry["timestamp"] < self.performance_cache.get("ttl", 3600):
                    self.performance_cache["cache_hits"] += 1
                    return cache_entry["result"]
            
            # Execute with timeout and monitoring
            self.performance_cache["cache_misses"] += 1
            self.performance_cache["total_commands"] += 1
            
            result = await asyncio.wait_for(
                msf_instance.execute_command(command),
                timeout=timeout
            )
            
            execution_time = time.time() - start_time
            
            # Update performance metrics
            if "command_times" not in self.performance_cache:
                self.performance_cache["command_times"] = {}
            
            if command not in self.performance_cache["command_times"]:
                self.performance_cache["command_times"][command] = []
            
            self.performance_cache["command_times"][command].append(execution_time)
            
            # Keep only last 100 measurements per command
            if len(self.performance_cache["command_times"][command]) > 100:
                self.performance_cache["command_times"][command] = \
                    self.performance_cache["command_times"][command][-100:]
            
            # Cache result if cache is enabled
            if "data" in self.performance_cache:
                # Implement LRU eviction if cache is full
                if len(self.performance_cache["data"]) >= self.performance_cache.get("max_size", 1000):
                    # Remove oldest entry
                    oldest_key = min(
                        self.performance_cache["data"].keys(),
                        key=lambda k: self.performance_cache["data"][k]["timestamp"]
                    )
                    del self.performance_cache["data"][oldest_key]
                
                self.performance_cache["data"][cache_key] = {
                    "result": result,
                    "timestamp": time.time(),
                    "execution_time": execution_time
                }
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Command '{command}' timed out after {timeout} seconds")
            return f"Error: Command timed out after {timeout} seconds"
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return f"Error: {str(e)}"
        finally:
            # Update average response time
            total_time = sum(
                sum(times) for times in self.performance_cache.get("command_times", {}).values()
            )
            total_commands = sum(
                len(times) for times in self.performance_cache.get("command_times", {}).values()
            )
            if total_commands > 0:
                self.performance_cache["avg_response_time"] = total_time / total_commands
    
    async def _suggest_framework_update(self):
        """Suggest framework update methods."""
        update_methods = [
            "apt update && apt upgrade metasploit-framework",
            "gem update metasploit-framework",
            "git pull (if installed from source)",
            "Download latest installer from https://metasploit.com"
        ]
        
        logger.warning("Framework update suggested. Methods:")
        for i, method in enumerate(update_methods, 1):
            logger.warning(f"  {i}. {method}")
    
    def _version_needs_update(self, version: str) -> bool:
        """Check if framework version needs update."""
        try:
            parts = [int(x) for x in version.split('.')]
            # Consider versions older than 6.3.0 as needing update
            return parts < [6, 3, 0]
        except Exception:
            return True  # If we can't parse, assume update needed
    
    def _find_executable(self, name: str) -> Optional[str]:
        """Find executable with common paths."""
        common_paths = [
            f"/usr/bin/{name}",
            f"/opt/metasploit-framework/bin/{name}",
            f"/usr/local/bin/{name}",
        ]
        
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        return shutil.which(name)
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            "framework_info": self.framework_info,
            "optimization_applied": self.optimization_applied,
            "cache_stats": {
                "hits": self.performance_cache.get("cache_hits", 0),
                "misses": self.performance_cache.get("cache_misses", 0),
                "hit_rate": (
                    self.performance_cache.get("cache_hits", 0) / 
                    max(1, self.performance_cache.get("cache_hits", 0) + self.performance_cache.get("cache_misses", 0))
                ) * 100
            },
            "command_stats": {
                "total_commands": self.performance_cache.get("total_commands", 0),
                "avg_response_time": self.performance_cache.get("avg_response_time", 0),
                "command_times": {
                    cmd: {
                        "count": len(times),
                        "avg": sum(times) / len(times),
                        "min": min(times),
                        "max": max(times)
                    }
                    for cmd, times in self.performance_cache.get("command_times", {}).items()
                    if times
                }
            },
            "parsing_patterns": len(self.parsing_patterns)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get current optimizer status."""
        return {
            "msf_path": self.msf_path,
            "msfvenom_path": self.msfvenom_path,
            "optimization_applied": self.optimization_applied,
            "framework_info": self.framework_info,
            "cache_size": len(self.performance_cache.get("data", {})),
            "performance_report": self.get_performance_report()
        }


# Usage example
async def test_optimizer():
    """Test the performance optimizer."""
    optimizer = MSFPerformanceOptimizer()
    init_result = await optimizer.initialize()
    print(f"Initialization result: {init_result}")
    print(f"Performance report: {optimizer.get_performance_report()}")
    print(f"Status: {optimizer.get_status()}")


if __name__ == "__main__":
    asyncio.run(test_optimizer())