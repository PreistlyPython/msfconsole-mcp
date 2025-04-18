#!/usr/bin/env python3

"""
MSF Execution Module for MCP
----------------------------
Provides enhanced execution and interaction with Metasploit Framework
"""

import os
import sys
import asyncio
import logging
import subprocess
import shlex
from typing import List, Dict, Any, Optional, Tuple

# Setup logging
logger = logging.getLogger("msf_execution")
logger.setLevel(logging.DEBUG)

class MSFConsoleExecutor:
    """A robust executor for Metasploit Framework commands with enhanced error handling."""
    
    def __init__(self, 
                 msf_path: Optional[str] = None, 
                 timeout: int = 60,
                 debug: bool = False):
        """Initialize the MSF executor.
        
        Args:
            msf_path: Path to msfconsole executable
            timeout: Default command timeout in seconds
            debug: Enable debug logging
        """
        self.msf_path = msf_path or self._find_msf_executable()
        self.timeout = timeout
        self.debug = debug
        
        # Validate MSF installation
        if not self.msf_path:
            logger.error("Metasploit Framework not found in PATH")
            raise FileNotFoundError("Metasploit Framework not found in PATH")
        
        logger.info(f"Using MSF at: {self.msf_path}")
    
    def _find_msf_executable(self) -> Optional[str]:
        """Find the Metasploit Framework executable in PATH."""
        import shutil
        return shutil.which("msfconsole")
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """Execute a Metasploit command and return the results.
        
        Args:
            command: MSF command to execute
            
        Returns:
            Dictionary with command results
        """
        try:
            logger.info(f"Executing MSF command: {command}")
            
            # Build the full command with proper error handling
            full_cmd = [self.msf_path, "-q", "-x", command, "-x", "exit"]
            
            # Execute the command as a subprocess
            process = await asyncio.create_subprocess_exec(
                *full_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Command timed out after {self.timeout}s: {command}")
                process.kill()
                return {
                    "success": False,
                    "error": f"Command timed out after {self.timeout} seconds",
                    "command": command
                }
            
            # Process output
            stdout_text = stdout.decode('utf-8', errors='replace').strip()
            stderr_text = stderr.decode('utf-8', errors='replace').strip()
            
            # Check for errors
            if process.returncode != 0:
                logger.error(f"Command failed with code {process.returncode}: {command}")
                logger.error(f"Error output: {stderr_text}")
                return {
                    "success": False,
                    "error": stderr_text or f"Command failed with exit code {process.returncode}",
                    "command": command,
                    "code": process.returncode
                }
            
            # Success case
            logger.info(f"Command completed successfully: {command}")
            return {
                "success": True,
                "output": stdout_text,
                "command": command
            }
            
        except Exception as e:
            logger.exception(f"Exception executing command {command}: {str(e)}")
            return {
                "success": False,
                "error": f"Exception: {str(e)}",
                "command": command
            }
    
    def get_version(self) -> Dict[str, Any]:
        """Get the Metasploit Framework version information synchronously."""
        try:
            # Simple subprocess call for version info
            result = subprocess.run(
                [self.msf_path, "-v"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Parse version information
                version_output = result.stdout.strip()
                version_lines = version_output.split('\n')
                version_info = {
                    "success": True,
                    "full_output": version_output,
                }
                
                # Extract the main version line
                if version_lines:
                    main_line = version_lines[0]
                    if "Metasploit Framework" in main_line:
                        # Extract the version number
                        parts = main_line.split('|')
                        if len(parts) > 1:
                            version_info["version"] = parts[0].strip().split()[-1]
                            version_info["build_date"] = parts[1].strip() if len(parts) > 1 else None
                
                return version_info
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "code": result.returncode
                }
                
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Timeout getting version information"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Simple test when run directly
if __name__ == "__main__":
    # Setup console logging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    try:
        executor = MSFConsoleExecutor(debug=True)
        version_info = executor.get_version()
        print(f"MSF Version Info: {version_info}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
