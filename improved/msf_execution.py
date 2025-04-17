#!/usr/bin/env python3

"""
Improved Metasploit Execution Class
-----------------------------------
This module provides a more reliable method for executing msfconsole commands
through resource scripts and shorter execution sessions.
"""

import os
import asyncio
import tempfile
import logging
import shlex
import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple

# Configure logging
logger = logging.getLogger(__name__)

class MSFConsoleExecutor:
    """
    Improved class for executing Metasploit commands that focuses on:
    - Using resource scripts for reliability
    - Shorter execution sessions to avoid hanging
    - Better error handling and timeouts
    """
    
    def __init__(self, msfconsole_path: str, msfvenom_path: str, config: Dict[str, Any]):
        """
        Initialize the MSFConsole executor with paths and configuration
        
        Args:
            msfconsole_path: Path to the msfconsole executable
            msfvenom_path: Path to the msfvenom executable
            config: Configuration dictionary
        """
        self.msfconsole_path = msfconsole_path
        self.msfvenom_path = msfvenom_path
        self.config = config
        self.current_workspace = config["metasploit"]["workspace"]
        self.temp_files = []  # Track temporary files for cleanup
        
        # Ensure paths exist
        if not os.path.exists(msfconsole_path):
            logger.warning(f"msfconsole not found at {msfconsole_path}")
        if not os.path.exists(msfvenom_path):
            logger.warning(f"msfvenom not found at {msfvenom_path}")
    
    def _validate_command(self, command: str) -> bool:
        """
        Validate if the command is allowed by security rules
        
        Args:
            command: Command to validate
            
        Returns:
            bool: True if command is allowed, False otherwise
        """
        security_config = self.config["security"]
        
        # Basic validation
        if not command or not command.strip():
            return False
        
        # Check for allowed command prefixes if enabled
        if security_config["validate_commands"] and security_config.get("allowed_commands"):
            command_parts = command.split(None, 1)[0].lower()
            if not any(command_parts.startswith(allowed) for allowed in security_config["allowed_commands"]):
                logger.warning(f"Command not in allowed list: {command}")
                return False
            
        # Check for disallowed modules
        use_match = re.search(r'use\s+(\S+)', command, re.IGNORECASE)
        if use_match:
            module_path = use_match.group(1)
            for disallowed in security_config["disallowed_modules"]:
                if module_path.startswith(disallowed):
                    logger.warning(f"Command includes disallowed module: {module_path}")
                    return False
        
        return True
    
    async def _ctx_info(self, ctx, message):
        """Helper method to handle info messages with ctx objects"""
        if hasattr(ctx, 'info'):
            await ctx.info(message)
        elif hasattr(ctx, 'send_info'):
            await ctx.send_info(message)
    
    async def _ctx_error(self, ctx, message):
        """Helper method to handle error messages with ctx objects"""
        if hasattr(ctx, 'error'):
            await ctx.error(message)
        elif hasattr(ctx, 'send_error'):
            await ctx.send_error(message)
    
    async def _ctx_progress(self, ctx, message, percentage):
        """Helper method to handle progress updates with ctx objects"""
        if hasattr(ctx, 'progress'):
            await ctx.progress(message, percentage)
        elif hasattr(ctx, 'report_progress'):
            await ctx.report_progress(percentage, 100, message)
    
    async def run_command(self, 
                          command: str, 
                          ctx: Any = None, 
                          timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Run a command in msfconsole using a resource script
        
        Args:
            command: Command to run
            ctx: MCP context for reporting progress
            timeout: Command timeout (overrides config value if provided)
            
        Returns:
            Dict with command result
        """
        if ctx:
            await self._ctx_info(ctx, f"Running command: {command}")
        
        # Use provided timeout or default from config
        cmd_timeout = timeout or self.config["security"]["command_timeout"]
        
        # Command validation
        if not self._validate_command(command):
            return {
                "success": False,
                "error": "Command validation failed. The command may contain disallowed modules or syntax."
            }
        
        # Create a temporary resource script file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.rc') as tmp:
            # Set the workspace
            if self.current_workspace and not command.startswith("workspace"):
                tmp.write(f"workspace {self.current_workspace}\n")
            
            # Write the command and exit
            tmp.write(f"{command}\n")
            tmp.write("exit\n")
            tmp_filename = tmp.name
            self.temp_files.append(tmp_filename)
        
        try:
            # Progress reporting
            if ctx:
                await self._ctx_progress(ctx, "Running msfconsole...", 30)
            
            # Run msfconsole with the resource script
            cmd = [self.msfconsole_path, "-q", "-r", tmp_filename]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Set up a timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cmd_timeout
                )
                
                if ctx:
                    await self._ctx_progress(ctx, "Command executed, processing output...", 70)
            except asyncio.TimeoutError:
                process.kill()
                if ctx:
                    await self._ctx_error(ctx, f"Command timed out after {cmd_timeout} seconds")
                return {
                    "success": False,
                    "error": f"Command execution timed out after {cmd_timeout} seconds"
                }
            
            # Process output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Check for workspace changes
            if command.startswith("workspace"):
                workspace_match = re.search(r'workspace\s+(\S+)', command, re.IGNORECASE)
                if workspace_match:
                    self.current_workspace = workspace_match.group(1)
            
            # Truncate long output if needed
            max_length = self.config["output"]["max_output_length"]
            truncation_msg = self.config["output"]["truncation_message"]
            
            if len(stdout_text) > max_length:
                stdout_text = stdout_text[:max_length] + truncation_msg
            
            # Final progress update
            if ctx:
                await self._ctx_progress(ctx, "Command completed", 100)
            
            # Create result dictionary
            result = {
                "success": True,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command,
                "return_code": process.returncode,
                "workspace": self.current_workspace
            }
            
            # Parse output for structured data
            self._parse_output(result, command, stdout_text)
            
            return result
        
        except Exception as e:
            logger.error(f"Error running msfconsole command: {e}")
            if ctx:
                await self._ctx_error(ctx, f"Error running command: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
        finally:
            # Clean up temp file if configured to do so
            if self.config["performance"]["cleanup_temp_files"]:
                try:
                    if tmp_filename in self.temp_files:
                        os.unlink(tmp_filename)
                        self.temp_files.remove(tmp_filename)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
    
    def _parse_output(self, result: Dict[str, Any], command: str, output: str) -> None:
        """
        Parse command output for structured data based on command type
        
        Args:
            result: Result dictionary to update with parsed data
            command: The original command that was executed
            output: The command output to parse
        """
        cmd_lower = command.lower()
        
        # Extract hosts information
        if "hosts" in cmd_lower:
            result["hosts"] = self._parse_hosts(output)
        
        # Extract services information
        if "services" in cmd_lower:
            result["services"] = self._parse_services(output)
        
        # Extract vulnerabilities information
        if "vulns" in cmd_lower:
            result["vulnerabilities"] = self._parse_vulns(output)
        
        # Extract session information
        if "sessions" in cmd_lower:
            result["sessions"] = self._parse_sessions(output)
        
        # Extract module information
        if cmd_lower.startswith("search "):
            result["modules"] = self._parse_search_results(output)
    
    def _parse_hosts(self, output: str) -> List[Dict[str, str]]:
        """
        Parse hosts from command output
        
        Args:
            output: Command output text
            
        Returns:
            List of host dictionaries
        """
        hosts = []
        lines = output.split('\n')
        
        # Find the header line
        header_line = -1
        headers = []
        
        for i, line in enumerate(lines):
            if 'address' in line.lower() and 'name' in line.lower():
                header_line = i
                headers = [h.strip() for h in re.split(r'\s{2,}', line.strip())]
                break
        
        if header_line == -1:
            return hosts
        
        # Process data lines
        for i in range(header_line + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines, headers, and dividers
            if not line or '====' in line or not line[0].isdigit():
                continue
            
            # Parse line into fields
            try:
                fields = re.split(r'\s{2,}', line)
                if len(fields) >= len(headers):
                    host = {headers[j]: fields[j] for j in range(len(headers))}
                    hosts.append(host)
            except Exception as e:
                logger.warning(f"Error parsing host line: {e}")
        
        return hosts
    
    def _parse_services(self, output: str) -> List[Dict[str, str]]:
        """
        Parse services from command output
        
        Args:
            output: Command output text
            
        Returns:
            List of service dictionaries
        """
        services = []
        lines = output.split('\n')
        
        # Find the header line
        header_line = -1
        headers = []
        
        for i, line in enumerate(lines):
            if 'port' in line.lower() and 'proto' in line.lower() and 'name' in line.lower():
                header_line = i
                headers = [h.strip() for h in re.split(r'\s{2,}', line.strip())]
                break
        
        if header_line == -1:
            return services
        
        # Process data lines
        for i in range(header_line + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines, headers, and dividers
            if not line or '====' in line or not line[0].isdigit():
                continue
            
            # Parse line into fields
            try:
                fields = re.split(r'\s{2,}', line)
                if len(fields) >= len(headers):
                    service = {headers[j]: fields[j] for j in range(len(headers))}
                    services.append(service)
            except Exception as e:
                logger.warning(f"Error parsing service line: {e}")
        
        return services
    
    def _parse_vulns(self, output: str) -> List[Dict[str, str]]:
        """
        Parse vulnerabilities from command output
        
        Args:
            output: Command output text
            
        Returns:
            List of vulnerability dictionaries
        """
        vulns = []
        lines = output.split('\n')
        
        # Find the header line
        header_line = -1
        headers = []
        
        for i, line in enumerate(lines):
            if 'host' in line.lower() and 'name' in line.lower() and 'info' in line.lower():
                header_line = i
                headers = [h.strip() for h in re.split(r'\s{2,}', line.strip())]
                break
        
        if header_line == -1:
            return vulns
        
        # Process data lines
        for i in range(header_line + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines, headers, and dividers
            if not line or '====' in line:
                continue
            
            # Parse line into fields
            try:
                fields = re.split(r'\s{2,}', line)
                if len(fields) >= len(headers):
                    vuln = {headers[j]: fields[j] for j in range(len(headers))}
                    vulns.append(vuln)
            except Exception as e:
                logger.warning(f"Error parsing vulnerability line: {e}")
        
        return vulns
    
    def _parse_sessions(self, output: str) -> List[Dict[str, str]]:
        """
        Parse active sessions from command output
        
        Args:
            output: Command output text
            
        Returns:
            List of session dictionaries
        """
        sessions = []
        lines = output.split('\n')
        
        # Find the header line
        header_line = -1
        headers = []
        
        for i, line in enumerate(lines):
            if 'id' in line.lower() and 'type' in line.lower() and 'information' in line.lower():
                header_line = i
                headers = [h.strip() for h in re.split(r'\s{2,}', line.strip())]
                break
        
        if header_line == -1:
            return sessions
        
        # Process data lines
        for i in range(header_line + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines, headers, and dividers
            if not line or '-' * 5 in line:
                continue
            
            # Parse line into fields - special handling for information field which may contain spaces
            try:
                fields = re.split(r'\s{2,}', line, maxsplit=len(headers)-1)
                if len(fields) >= len(headers):
                    session = {headers[j]: fields[j] for j in range(len(headers))}
                    sessions.append(session)
            except Exception as e:
                logger.warning(f"Error parsing session line: {e}")
        
        return sessions
    
    def _parse_search_results(self, output: str) -> List[Dict[str, str]]:
        """
        Parse search results from command output
        
        Args:
            output: Command output text
            
        Returns:
            List of module dictionaries
        """
        modules = []
        lines = output.split('\n')
        
        # Find the header line
        header_line = -1
        headers = []
        
        for i, line in enumerate(lines):
            if '#' in line and 'name' in line.lower() and 'disclosure date' in line.lower():
                header_line = i
                headers = [h.strip() for h in re.split(r'\s{2,}', line.strip())]
                break
        
        if header_line == -1:
            return modules
        
        # Process data lines
        for i in range(header_line + 1, len(lines)):
            line = lines[i].strip()
            
            # Skip empty lines and dividers
            if not line or '=======' in line:
                continue
            
            # Parse line into fields
            try:
                # Handle the fact that description may contain spaces
                fields = []
                parts = re.split(r'\s{2,}', line, maxsplit=len(headers)-2)
                
                # Only process lines that look like module entries
                if parts and parts[0].strip() and parts[0][0].isdigit():
                    for j in range(len(parts)):
                        fields.append(parts[j].strip())
                    
                    if len(fields) >= len(headers) - 1:  # Account for potential missing description
                        module = {}
                        for j in range(len(fields)):
                            if j < len(headers):
                                module[headers[j]] = fields[j]
                        modules.append(module)
            except Exception as e:
                logger.warning(f"Error parsing search result line: {e}")
        
        return modules
    
    async def run_msfvenom(self, 
                           params: List[str], 
                           ctx: Any = None, 
                           timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Run msfvenom with given parameters
        
        Args:
            params: List of parameters for msfvenom
            ctx: MCP context for reporting progress
            timeout: Command timeout (overrides config value if provided)
            
        Returns:
            Dict with command result
        """
        if ctx:
            await self._ctx_info(ctx, f"Running msfvenom with params: {' '.join(params)}")
        
        # Use provided timeout or default from config
        cmd_timeout = timeout or self.config["security"]["command_timeout"]
        
        try:
            # Progress reporting
            if ctx:
                await self._ctx_progress(ctx, "Generating payload...", 30)
            
            # Run msfvenom
            cmd = [self.msfvenom_path] + params
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Set up a timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=cmd_timeout
                )
                
                if ctx:
                    await self._ctx_progress(ctx, "Payload generated, processing output...", 70)
            except asyncio.TimeoutError:
                process.kill()
                if ctx:
                    await self._ctx_error(ctx, f"msfvenom command timed out after {cmd_timeout} seconds")
                return {
                    "success": False,
                    "error": f"Command execution timed out after {cmd_timeout} seconds"
                }
            
            # Process output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Truncate long output if needed
            max_length = self.config["output"]["max_output_length"]
            truncation_msg = self.config["output"]["truncation_message"]
            
            if len(stdout_text) > max_length:
                stdout_text = stdout_text[:max_length] + truncation_msg
            
            # Final progress update
            if ctx:
                await self._ctx_progress(ctx, "Payload generation completed", 100)
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode
            }
        
        except Exception as e:
            logger.error(f"Error running msfvenom: {e}")
            if ctx:
                await self._ctx_error(ctx, f"Error running msfvenom: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_version(self, ctx: Any = None) -> Dict[str, Any]:
        """
        Get Metasploit Framework version
        
        Args:
            ctx: MCP context for reporting progress
            
        Returns:
            Dict with version information
        """
        try:
            if ctx:
                await self._ctx_info(ctx, "Getting Metasploit Framework version")
                await self._ctx_progress(ctx, "Checking version...", 50)
            
            # Run msfconsole with version flag
            cmd = [self.msfconsole_path, "-v"]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Use a shorter timeout for version check
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=10  # Short timeout for version check
            )
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Extract version from output
            version_match = re.search(r'Framework: (\d+\.\d+\.\d+[-\w]*)', stdout_text)
            if version_match:
                version = version_match.group(1)
            else:
                version = "Unknown"
            
            if ctx:
                await self._ctx_progress(ctx, "Version check completed", 100)
            
            return {
                "success": True,
                "version": version,
                "full_output": stdout_text
            }
        except Exception as e:
            logger.error(f"Error getting Metasploit version: {e}")
            if ctx:
                await self._ctx_error(ctx, f"Error getting Metasploit version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_db_status(self, ctx: Any = None) -> Dict[str, Any]:
        """
        Check if the database is connected
        
        Args:
            ctx: MCP context for reporting progress
            
        Returns:
            Dict with database status
        """
        try:
            if ctx:
                await self._ctx_info(ctx, "Checking database status")
                await self._ctx_progress(ctx, "Checking database connection...", 50)
            
            # Run db_status command
            result = await self.run_command("db_status", ctx, 
                                          timeout=self.config["metasploit"]["database_timeout"])
            
            if result["success"]:
                db_connected = "connected" in result["stdout"].lower()
                
                if ctx:
                    if db_connected:
                        await self._ctx_info(ctx, "Database is connected")
                    else:
                        await self._ctx_info(ctx, "Database is not connected")
                    await self._ctx_progress(ctx, "Database check completed", 100)
                
                return {
                    "success": True,
                    "db_connected": db_connected,
                    "output": result["stdout"]
                }
            else:
                if ctx:
                    await self._ctx_error(ctx, "Failed to check database status")
                    await self._ctx_progress(ctx, "Database check failed", 100)
                
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error checking database status"),
                    "output": result.get("stdout", "")
                }
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            if ctx:
                await self._ctx_error(ctx, f"Error checking database status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cleanup(self):
        """
        Clean up any remaining temporary files
        """
        for tmp_file in self.temp_files[:]:
            try:
                if os.path.exists(tmp_file):
                    os.unlink(tmp_file)
                self.temp_files.remove(tmp_file)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary file {tmp_file}: {e}")
