#!/usr/bin/env python3

"""
Metasploit Framework Console (msfconsole) MCP Module
---------------------------------------------------
This module provides tools for interacting with Metasploit Framework's msfconsole through MCP.
It wraps msfconsole functionality in a structured way, making it accessible to LLMs.
"""

import os
import sys
import logging
import importlib.metadata
# Import asyncio patch for Python 3.11+ compatibility
try:
    import asyncio_patch
    ASYNCIO_PATCHED = asyncio_patch.apply_patches()
except ImportError:
    ASYNCIO_PATCHED = False

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("msfconsole_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Function to check for required packages
def check_required_packages():
    """Check if required packages are installed and return version info"""
    required_packages = ["mcp", "typing-extensions"]
    package_info = {}
    missing_packages = []
    
    for package in required_packages:
        try:
            version = importlib.metadata.version(package)
            package_info[package] = version
            logger.info(f"Found package {package} version {version}")
        except importlib.metadata.PackageNotFoundError:
            missing_packages.append(package)
            logger.error(f"Required package {package} not found")
    
    if missing_packages:
        logger.error(f"Missing required packages: {', '.join(missing_packages)}")
        return False, package_info
    
    return True, package_info

# Check Python version compatibility
import platform
python_version = platform.python_version_tuple()
python_version_str = '.'.join(python_version)

logger.info(f"Python version: {python_version_str}")

# Warn about Python 3.12 compatibility issues
if int(python_version[0]) == 3 and int(python_version[1]) >= 12:
    logger.warning(f"Python {python_version_str} may have compatibility issues with MCP. Python 3.8 or 3.9 is recommended.")
    print(f"WARNING: Python {python_version_str} may have compatibility issues with MCP. Python 3.8 or 3.9 is recommended.")
    print("If you encounter issues, please run ./fix_python_version.sh to set up a compatible environment.")

# Check for required packages
packages_ok, package_versions = check_required_packages()
if not packages_ok:
    sys.stderr.write(f"ERROR: Missing required packages. Please install the dependencies listed in requirements.txt\n")
    logger.error("Attempting to continue despite missing packages...")

# Now import the rest after logging is set up
import asyncio
import json
import re
import subprocess
import tempfile
import shlex
import shutil
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime

# Import documentation tools
from doc_tools import list_available_docs, get_document_content, list_commands

# Import SafeContext for better error handling
from safe_context import SafeContext

# Try importing MCP SDK with better error handling
FastMCP = None
Context = None
MCP_VERSION = "unknown"

try:
    from mcp.server.fastmcp import FastMCP, Context
    try:
        import mcp
        MCP_VERSION = getattr(mcp, "__version__", "unknown")
        logger.info(f"Successfully imported MCP SDK version {MCP_VERSION}")
    except (ImportError, AttributeError):
        logger.warning("Could not determine MCP SDK version")
except ImportError as e:
    logger.error(f"MCP SDK import error: {e}")
    sys.stderr.write(f"ERROR: MCP SDK import error: {e}\n")
    
    # Try to provide more helpful error messages
    error_msg = str(e)
    if "No module named 'mcp'" in error_msg:
        sys.stderr.write("\nMCP SDK not found in Python path. Please ensure the mcp package is installed.\n")
        sys.stderr.write("Run: ./fix_python_version.sh to set up a compatible environment\n")
    elif "async" in error_msg and python_version_str.startswith("3.12"):
        sys.stderr.write("\nPython 3.12 compatibility issue detected. 'async' keyword error.\n")
        sys.stderr.write("Run: ./fix_python_version.sh to set up an environment with Python 3.8 or 3.9\n")
    sys.exit(1)
except SyntaxError as e:
    logger.error(f"Syntax error in MCP SDK: {e}")
    sys.stderr.write(f"ERROR: Syntax error in MCP SDK: {e}\n")
    if python_version_str.startswith("3.12"):
        sys.stderr.write("\nPython 3.12 compatibility issue detected. Please use Python 3.8 or 3.9.\n")
        sys.stderr.write("Run: ./fix_python_version.sh to set up a compatible environment\n")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error importing MCP SDK: {e}")
    sys.stderr.write(f"ERROR: Unexpected error importing MCP SDK: {e}\n")
    sys.exit(1)

# Define version
VERSION = "0.1.0"

# Initialize FastMCP server with more error handling
try:
    mcp = FastMCP("msfconsole", version=VERSION)
    logger.info(f"Successfully initialized FastMCP server version {VERSION}")
except Exception as e:
    logger.error(f"Failed to initialize FastMCP server: {e}")
    sys.stderr.write(f"ERROR: Failed to initialize FastMCP server: {e}\n")
    sys.exit(1)

# Load configuration
# Load configuration
try:
    from config import CONFIG, PY_COMPATIBILITY_FIXES
    logger.info("Loaded configuration from config.py")
except ImportError:
    logger.warning("No config.py found, using defaults")
    # Default configuration settings
    CONFIG = {
        # Metasploit Framework settings
        "metasploit": {
            "msfconsole_path": shutil.which("msfconsole") or "/usr/bin/msfconsole",
            "msfvenom_path": shutil.which("msfvenom") or "/usr/bin/msfvenom",
            "workspace": "default",  # Default Metasploit workspace
        },
        
        # Security settings
        "security": {
            "command_timeout": 120,  # Maximum time (seconds) a command can run
            "disallowed_modules": [],  # Dangerous modules to block
            "validate_commands": True,  # Whether to validate commands before running
        },
        
        # Output settings
        "output": {
            "max_output_length": 50000,  # Maximum length of command output to return
            "truncation_message": "\n[... Output truncated due to length ...]",
        },
    }
    
    PY_COMPATIBILITY_FIXES = {
        "asyncio_fix": True,  # Enable fixes for asyncio in Python 3.12+
    }
    def __init__(self, msfconsole_path: str, msfvenom_path: str):
        self.msfconsole_path = msfconsole_path
        self.msfvenom_path = msfvenom_path
        self.current_workspace = CONFIG["metasploit"]["workspace"]
    
    def _validate_command(self, command: str) -> bool:
        """
        Validate if the command is allowed by security rules
        
        Args:
            command: Command to validate
            
        Returns:
            bool: True if command is allowed, False otherwise
        """
        # Basic validation
        if not command or not command.strip():
            return False
            
        # Check for disallowed use module commands
        use_match = re.search(r'use\s+(\S+)', command, re.IGNORECASE)
        if use_match:
            module_path = use_match.group(1)
            # Check if module path is allowed
            for disallowed in CONFIG["security"]["disallowed_modules"]:
                if module_path.startswith(disallowed):
                    logger.warning(f"Command includes disallowed module: {module_path}")
                    return False
        
        return True
    
    async def run_command(self, command: str, ctx: Context = None) -> Dict[str, Any]:
        """
        Run a command in msfconsole
        
        Args:
            command: Command to run
            ctx: MCP context for reporting progress
            
        Returns:
            Dict with command result
        """
        if ctx:
            await ctx.info(f"Running command: {command}")
            
        if not self._validate_command(command):
            return {
                "success": False,
                "error": "Command validation failed. The command may contain disallowed modules or syntax."
            }
            
        # Create a temporary script file
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.rc') as tmp:
            # Set the workspace if it's not the current command
            if self.current_workspace and not command.startswith("workspace"):
                tmp.write(f"workspace {self.current_workspace}\n")
            tmp.write(f"{command}\n")
            tmp.write("exit\n")
            tmp_filename = tmp.name
            
        try:
            # Run msfconsole with the resource script
            cmd = [self.msfconsole_path, "-q", "-r", tmp_filename]
            
            if ctx:
                await ctx.info(f"Executing msfconsole with resource script")
                await ctx.progress("Running command...", 50)
                
            process = await asyncio.create_subprocess_exec(
                *cmd,
                    stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Set up a timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=CONFIG["security"]["command_timeout"]
                )
            except asyncio.TimeoutError:
                process.kill()
                if ctx:
                    await ctx.error(f"Command timed out after {CONFIG['security']['command_timeout']} seconds")
                return {
                    "success": False,
                    "error": f"Command execution timed out after {CONFIG['security']['command_timeout']} seconds"
                }
                
            # Process output
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            if ctx:
                await ctx.progress("Processing results...", 90)
            
            # Check for workspace changes
            if command.startswith("workspace"):
                workspace_match = re.search(r'workspace\s+(\S+)', command, re.IGNORECASE)
                if workspace_match:
                    new_workspace = workspace_match.group(1)
                    self.current_workspace = new_workspace
            
            # Truncate long output if needed
            if len(stdout_text) > CONFIG["output"]["max_output_length"]:
                stdout_text = stdout_text[:CONFIG["output"]["max_output_length"]] + CONFIG["output"]["truncation_message"]
            
            if ctx:
                await ctx.progress("Command completed", 100)
            
            result = {
                "success": True,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command,
                "return_code": process.returncode,
                "workspace": self.current_workspace
            }
            
            # Parse output for hosts, services, etc.
            if "hosts" in command:
                result["hosts"] = self._parse_hosts(stdout_text)
            if "services" in command:
                result["services"] = self._parse_services(stdout_text)
            if "vulns" in command:
                result["vulnerabilities"] = self._parse_vulns(stdout_text)
            if "sessions" in command:
                result["sessions"] = self._parse_sessions(stdout_text)
                
            return result
            
        except Exception as e:
            logger.error(f"Error running msfconsole command: {e}")
            if ctx:
                await ctx.error(f"Error running command: {e}")
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_filename)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file: {e}")
    
    async def run_msfvenom(self, params: List[str], ctx: Context = None) -> Dict[str, Any]:
        """
        Run msfvenom with given parameters
        
        Args:
            params: List of parameters for msfvenom
            ctx: MCP context for reporting progress
            
        Returns:
            Dict with command result
        """
        if ctx:
            await ctx.info(f"Running msfvenom with params: {' '.join(params)}")
            
        try:
            cmd = [self.msfvenom_path] + params
            
            if ctx:
                await ctx.progress("Generating payload...", 30)
                
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=CONFIG["security"]["command_timeout"]
            )
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            if ctx:
                await ctx.progress("Payload generation complete", 100)
            
            # Truncate long output if needed
            if len(stdout_text) > CONFIG["output"]["max_output_length"]:
                stdout_text = stdout_text[:CONFIG["output"]["max_output_length"]] + CONFIG["output"]["truncation_message"]
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            if ctx:
                await ctx.error(f"msfvenom command timed out after {CONFIG['security']['command_timeout']} seconds")
            return {
                "success": False,
                "error": f"Command execution timed out after {CONFIG['security']['command_timeout']} seconds"
            }
        except Exception as e:
            logger.error(f"Error running msfvenom: {e}")
            if ctx:
                await ctx.error(f"Error running msfvenom: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _parse_hosts(self, output: str) -> List[Dict[str, str]]:
        """Parse hosts from command output"""
        hosts = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'address' in line.lower() and 'name' in line.lower() and 'os_name' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return hosts
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Hosts" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            host = {headers[i]: values[i] for i in range(len(headers))}
                            hosts.append(host)
                    except Exception as e:
                        logger.warning(f"Error parsing host line: {e}")
        
        return hosts
    
    def _parse_services(self, output: str) -> List[Dict[str, str]]:
        """Parse services from command output"""
        services = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'port' in line.lower() and 'proto' in line.lower() and 'name' in line.lower() and 'state' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return services
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Services" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            service = {headers[i]: values[i] for i in range(len(headers))}
                            services.append(service)
                    except Exception as e:
                        logger.warning(f"Error parsing service line: {e}")
        
        return services
        
    def _parse_vulns(self, output: str) -> List[Dict[str, str]]:
        """Parse vulnerabilities from command output"""
        vulns = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'host' in line.lower() and 'name' in line.lower() and 'info' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return vulns
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Vulnerabilities" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            vuln = {headers[i]: values[i] for i in range(len(headers))}
                            vulns.append(vuln)
                    except Exception as e:
                        logger.warning(f"Error parsing vulnerability line: {e}")
        
        return vulns
    
    def _parse_sessions(self, output: str) -> List[Dict[str, str]]:
        """Parse active sessions from command output"""
        sessions = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'id' in line.lower() and 'type' in line.lower() and 'information' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return sessions
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '-' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('-') and not "Active sessions" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip(), maxsplit=len(headers)-1)]
                        if len(values) >= len(headers):
                            session = {headers[i]: values[i] for i in range(len(headers))}
                            sessions.append(session)
                    except Exception as e:
                        logger.warning(f"Error parsing session line: {e}")
        
        return sessions
    
    async def get_version(self, ctx: Context = None) -> Dict[str, Any]:
        """Get Metasploit Framework version"""
        try:
            if ctx:
                await ctx.info("Getting Metasploit Framework version")
                
            cmd = [self.msfconsole_path, "-v"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Extract version from output
            version_match = re.search(r'Framework: (\d+\.\d+\.\d+[-\w]*)', stdout_text)
            if version_match:
                version = version_match.group(1)
            else:
                version = "Unknown"
                
            return {
                "success": True,
                "version": version,
                "full_output": stdout_text
            }
        except Exception as e:
            logger.error(f"Error getting Metasploit version: {e}")
            if ctx:
                await ctx.error(f"Error getting Metasploit version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_db_status(self, ctx: Context = None) -> Dict[str, Any]:
        """Check if the database is connected"""
        try:
            if ctx:
                await ctx.info("Checking database status")
                
            result = await self.run_command("db_status", ctx)
            
            if result["success"]:
                db_connected = "connected" in result["stdout"].lower()
                return {
                    "success": True,
                    "db_connected": db_connected,
                    "output": result["stdout"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error checking database status")
                }
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            if ctx:
                await ctx.error(f"Error checking database status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            if ctx:
                await ctx.progress("Payload generation complete", 100)
            
            # Truncate long output if needed
            if len(stdout_text) > CONFIG["output"]["max_output_length"]:
                stdout_text = stdout_text[:CONFIG["output"]["max_output_length"]] + CONFIG["output"]["truncation_message"]
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": process.returncode
            }
            
        except asyncio.TimeoutError:
            if ctx:
                await ctx.error(f"msfvenom command timed out after {CONFIG['security']['command_timeout']} seconds")
            return {
                "success": False,
                "error": f"Command execution timed out after {CONFIG['security']['command_timeout']} seconds"
            }
        except Exception as e:
            logger.error(f"Error running msfvenom: {e}")
            if ctx:
                await ctx.error(f"Error running msfvenom: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def _parse_hosts(self, output: str) -> List[Dict[str, str]]:
        """Parse hosts from command output"""
        hosts = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'address' in line.lower() and 'name' in line.lower() and 'os_name' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return hosts
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Hosts" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            host = {headers[i]: values[i] for i in range(len(headers))}
                            hosts.append(host)
                    except Exception as e:
                        logger.warning(f"Error parsing host line: {e}")
        
        return hosts
    
    def _parse_services(self, output: str) -> List[Dict[str, str]]:
        """Parse services from command output"""
        services = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'port' in line.lower() and 'proto' in line.lower() and 'name' in line.lower() and 'state' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return services
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Services" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            service = {headers[i]: values[i] for i in range(len(headers))}
                            services.append(service)
                    except Exception as e:
                        logger.warning(f"Error parsing service line: {e}")
        
        return services
        
    def _parse_vulns(self, output: str) -> List[Dict[str, str]]:
        """Parse vulnerabilities from command output"""
        vulns = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'host' in line.lower() and 'name' in line.lower() and 'info' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return vulns
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '===' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('=') and not "Vulnerabilities" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip())]
                        if len(values) >= len(headers):
                            vuln = {headers[i]: values[i] for i in range(len(headers))}
                            vulns.append(vuln)
                    except Exception as e:
                        logger.warning(f"Error parsing vulnerability line: {e}")
        
        return vulns
    
    def _parse_sessions(self, output: str) -> List[Dict[str, str]]:
        """Parse active sessions from command output"""
        sessions = []
        lines = output.split('\n')
        header_line = -1
        headers = []
        
        # Find the header line
        for i, line in enumerate(lines):
            if 'id' in line.lower() and 'type' in line.lower() and 'information' in line.lower():
                header_line = i
                header_text = line.strip()
                # Split based on multiple spaces
                headers = [h.strip() for h in re.split(r'\s{2,}', header_text)]
                break
                
        if header_line == -1:
            return sessions
            
        # Look for the divider line
        divider_line = header_line + 1
        if divider_line < len(lines) and '-' in lines[divider_line]:
            # Start processing from the line after the divider
            for line in lines[divider_line + 1:]:
                if line.strip() and not line.startswith('-') and not "Active sessions" in line:
                    try:
                        values = [v.strip() for v in re.split(r'\s{2,}', line.strip(), maxsplit=len(headers)-1)]
                        if len(values) >= len(headers):
                            session = {headers[i]: values[i] for i in range(len(headers))}
                            sessions.append(session)
                    except Exception as e:
                        logger.warning(f"Error parsing session line: {e}")
        
        return sessions
    
    async def get_version(self, ctx: Context = None) -> Dict[str, Any]:
        """Get Metasploit Framework version"""
        try:
            if ctx:
                await ctx.info("Getting Metasploit Framework version")
                
            cmd = [self.msfconsole_path, "-v"]
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            # Extract version from output
            version_match = re.search(r'Framework: (\d+\.\d+\.\d+[-\w]*)', stdout_text)
            if version_match:
                version = version_match.group(1)
            else:
                version = "Unknown"
                
            return {
                "success": True,
                "version": version,
                "full_output": stdout_text
            }
        except Exception as e:
            logger.error(f"Error getting Metasploit version: {e}")
            if ctx:
                await ctx.error(f"Error getting Metasploit version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_db_status(self, ctx: Context = None) -> Dict[str, Any]:
        """Check if the database is connected"""
        try:
            if ctx:
                await ctx.info("Checking database status")
                
            result = await self.run_command("db_status", ctx)
            
            if result["success"]:
                db_connected = "connected" in result["stdout"].lower()
                return {
                    "success": True,
                    "db_connected": db_connected,
                    "output": result["stdout"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error checking database status")
                }
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            if ctx:
                await ctx.error(f"Error checking database status: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Initialize the MSF console service

class MSFConsoleService:
    """
    Service for interacting with Metasploit Console.
    Handles executing commands and managing the msf console process.
    """
    def __init__(self, msfconsole_path, msfvenom_path):
        """
        Initialize the MSFConsole service with paths to required executables.
        
        Args:
            msfconsole_path: Path to the msfconsole executable
            msfvenom_path: Path to the msfvenom executable
        """
        self.msfconsole_path = msfconsole_path
        self.msfvenom_path = msfvenom_path
        self.process = None
        self.workspace = None
        
    async def start_console(self):
        """
        Start the Metasploit console process.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        import asyncio
        import shlex
        
        if self.process and self.process.returncode is None:
            # Process is already running
            return True
            
        try:
            cmd = shlex.split(self.msfconsole_path)
            self.process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Error starting MSF console: {e}")
            return False
            
    async def execute_command(self, command, timeout=60):
        """
        Execute a command in the Metasploit console.
        
        Args:
            command: Command to execute
            timeout: Timeout in seconds
            
        Returns:
            dict: Result containing success status and output or error
        """
        import asyncio
        
        if not self.process or self.process.returncode is not None:
            success = await self.start_console()
            if not success:
                return {
                    "success": False,
                    "error": "Failed to start MSF console"
                }
                
        try:
            # Write command to stdin
            self.process.stdin.write(f"{command}\n".encode())
            await self.process.stdin.drain()
            
            # Read output with timeout
            output = await asyncio.wait_for(
                self.process.stdout.read(4096),
                timeout=timeout
            )
            
            return {
                "success": True,
                "output": output.decode()
            }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing command: {e}"
            }
            
    async def close(self):
        """Close the Metasploit console process."""
        if self.process and self.process.returncode is None:
            try:
                self.process.terminate()
                await self.process.wait()
            except Exception as e:
                print(f"Error closing MSF console: {e}")

msf_service = MSFConsoleService(
    CONFIG["metasploit"]["msfconsole_path"], 
    CONFIG["metasploit"]["msfvenom_path"]
)

# Helper function to check if Metasploit is installed
async def check_metasploit_installed(ctx=None) -> bool:
    """
    Check if Metasploit Framework is installed and accessible.
    
    Args:
        ctx: MCP context for reporting progress (can be Context or SafeContext)
        
    Returns:
        bool: True if Metasploit is installed, False otherwise
    """
    # Ensure ctx is a SafeContext instance
    if ctx is not None and not isinstance(ctx, SafeContext):
        ctx = SafeContext(ctx)
    else:
        ctx = ctx or SafeContext(None)
    
    # Path check
    if not os.path.exists(msf_service.msfconsole_path):
        await ctx.error(f"msfconsole not found at {msf_service.msfconsole_path}")
        
        # Try to find it in PATH as a fallback
        msf_path = shutil.which("msfconsole")
        if msf_path:
            await ctx.info(f"Found alternative msfconsole in PATH at {msf_path}")
            msf_service.msfconsole_path = msf_path
        else:
            await ctx.error("msfconsole not found in PATH either")
            return False
    
    # Version check with progress reporting    
    try:
        await ctx.info("Checking Metasploit version")
        await ctx.report_progress(50, 100, "Verifying Metasploit installation...")
        
        result = await msf_service.get_version(ctx)
        
        if not result["success"]:
            await ctx.error("Failed to get Metasploit version")
            await ctx.report_progress(100, 100, "Verification failed")
            return False
            
        # Extract and log version info
        version = result.get("version", "Unknown")
        await ctx.info(f"Metasploit Framework version {version} detected")
        await ctx.report_progress(100, 100, "Verification successful")
        return True
    except Exception as e:
        await ctx.error(f"Error checking Metasploit installation: {e}")
        return False

# MCP Tool: Get Metasploit Framework version
@mcp.tool()
async def get_msf_version(ctx: Context = None) -> str:
    """
    Get the installed Metasploit Framework version.
    
    Returns:
        Version information and details
    """
    # Use SafeContext for better compatibility
    safe_ctx = SafeContext(ctx)
    
    # Log the request
    await safe_ctx.info("Request to get Metasploit Framework version")
    
    # Check if Metasploit is installed
    if not await check_metasploit_installed(safe_ctx):
        await safe_ctx.error("Metasploit Framework not found")
        return "Metasploit Framework not found. Please ensure it is installed."
        
    # Get version
    await safe_ctx.info("Getting Metasploit Framework version")
    version_result = await msf_service.get_version(safe_ctx)
    
    if version_result["success"]:
        version_output = version_result["full_output"]
        await safe_ctx.info(f"Successfully retrieved Metasploit version")
        return f"Metasploit Framework Version Information:\n\n{version_output}"
    else:
        error_msg = version_result.get('error', 'Unknown error')
        await safe_ctx.error(f"Failed to get version: {error_msg}")
        return f"Failed to get Metasploit Framework version: {error_msg}"


# MCP Tool: Execute msfconsole command
@mcp.tool()
async def run_msf_command(ctx: Context = None, command: str = "") -> str:
    """
    Execute a command in msfconsole.
    
    Args:
        command: The command to execute in msfconsole
    
    Returns:
        Command output
    """
    # Use SafeContext for better compatibility
    safe_ctx = SafeContext(ctx)
    
    # Log the request
    await safe_ctx.info(f"Request to execute msfconsole command: {command}")
    
    # Check if Metasploit is installed
    if not await check_metasploit_installed(safe_ctx):
        await safe_ctx.error("Metasploit Framework not found")
        return "Metasploit Framework not found. Please ensure it is installed."
    
    if not command:
        await safe_ctx.warning("No command provided")
        return "Please provide a command to execute."
    
    # Check command for safety
    if not msf_service._validate_command(command):
        await safe_ctx.error(f"Command validation failed: {command}")
        return "Command validation failed. The command may contain disallowed modules or syntax."
        
    # Run the command
    await safe_ctx.info(f"Executing command: {command}")
    await safe_ctx.report_progress(30, 100, "Executing command...")
    
    result = await msf_service.run_command(command, safe_ctx)
    
    await safe_ctx.report_progress(90, 100, "Processing results...")
    
    if result["success"]:
        await safe_ctx.info(f"Command executed successfully")
        output = f"Command: {command}\n"
        output += f"Workspace: {result['workspace']}\n\n"
        output += result["stdout"]
        
        if result["stderr"]:
            await safe_ctx.warning(f"Command generated warnings or errors")
            output += f"\nErrors/Warnings:\n{result['stderr']}"
        
        await safe_ctx.report_progress(100, 100, "Command completed")
        return output
    else:
        error_msg = result.get("error", "Unknown error")
        await safe_ctx.error(f"Failed to execute command: {error_msg}")
        return f"Failed to execute command: {error_msg}"


# MCP Tool: Search for modules
@mcp.tool()
async def search_modules(ctx: Context = None, query: str = "") -> str:
    """
    Search for modules in the Metasploit Framework.
    
    Args:
        query: Search query (e.g., 'ms17_010', 'type:exploit platform:windows')
    
    Returns:
        List of matching modules
    """
    # Use SafeContext for better compatibility
    safe_ctx = SafeContext(ctx)
    
    # Log the request
    await safe_ctx.info(f"Request to search for modules with query: {query}")
    
    # Check if Metasploit is installed
    if not await check_metasploit_installed(safe_ctx):
        await safe_ctx.error("Metasploit Framework not found")
        return "Metasploit Framework not found. Please ensure it is installed."
    
    if not query:
        await safe_ctx.warning("No search query provided")
        return "Please provide a search query."
    
    # Sanitize query for safety
    sanitized_query = query.replace(";", "").replace("|", "").replace("&", "")
    if sanitized_query != query:
        await safe_ctx.warning(f"Query was sanitized for safety: {query} -> {sanitized_query}")
    
    # Run the search command with progress reporting
    await safe_ctx.info(f"Searching for modules with query: {sanitized_query}")
    await safe_ctx.report_progress(30, 100, "Searching modules...")
    
    command = f"search {sanitized_query}"
    result = await msf_service.run_command(command, safe_ctx)
    
    await safe_ctx.report_progress(80, 100, "Processing search results...")
    
    if result["success"]:
        # Count matches for better feedback
        output_lines = result['stdout'].strip().split('\n')
        match_count = sum(1 for line in output_lines if line.strip() and not line.startswith('#') and not '=======' in line)
        
        await safe_ctx.info(f"Search completed, found {match_count} matching modules")
        await safe_ctx.report_progress(100, 100, f"Found {match_count} modules")
        
        return f"Search results for '{sanitized_query}':\n\n{result['stdout']}"
    else:
        error_msg = result.get("error", "Unknown error")
        await safe_ctx.error(f"Search failed: {error_msg}")
        return f"Failed to search for modules: {error_msg}"

# MCP Tool: List and manage workspaces
@mcp.tool()
async def manage_workspaces(ctx: Context = None, command: str = "list", workspace_name: str = "") -> str:
    """
    List and manage Metasploit workspaces.
    
    Args:
        command: Action to perform (list, add, delete, select)
        workspace_name: Name of the workspace for add/delete/select actions
    
    Returns:
        Result of the workspace operation
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    # Check database status
    db_status = await msf_service.check_db_status(ctx)
    if not db_status["success"] or not db_status.get("db_connected", False):
        return "Database is not connected. Workspaces require a connected database."
    
    # Prepare the command
    if command == "list":
        msf_command = "workspace"
    elif command == "add" and workspace_name:
        msf_command = f"workspace -a {workspace_name}"
    elif command == "delete" and workspace_name:
        msf_command = f"workspace -d {workspace_name}"
    elif command == "select" and workspace_name:
        msf_command = f"workspace {workspace_name}"
    else:
        return "Invalid workspace command. Use 'list', 'add', 'delete', or 'select'."
    
    # Run the command
    result = await msf_service.run_command(msf_command, ctx)
    
    if result["success"]:
        if command == "list":
            return f"Available workspaces:\n\n{result['stdout']}"
        elif command == "add":
            return f"Workspace '{workspace_name}' added.\n\n{result['stdout']}"
        elif command == "delete":
            return f"Workspace '{workspace_name}' deleted.\n\n{result['stdout']}"
        elif command == "select":
            return f"Switched to workspace '{workspace_name}'.\n\n{result['stdout']}"
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Failed to {command} workspace: {error_msg}"


# MCP Tool: Run a scan
@mcp.tool()
async def run_scan(ctx: Context = None, scan_type: str = "ping", target: str = "", options: str = "") -> str:
    """
    Run a scan against target hosts.
    
    Args:
        scan_type: Type of scan (ping, port, service, vuln)
        target: Target IP address, range, or subnet (e.g., '192.168.1.1', '192.168.1.0/24')
        options: Additional options for the scan
    
    Returns:
        Scan results
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    if not target:
        return "Please provide a target for the scan."
    
    # Choose scan module based on scan_type
    scan_module = ""
    if scan_type == "ping":
        scan_module = "auxiliary/scanner/discovery/arp_sweep"
    elif scan_type == "port":
        scan_module = "auxiliary/scanner/portscan/tcp"
    elif scan_type == "service":
        scan_module = "auxiliary/scanner/discovery/udp_sweep"
    elif scan_type == "vuln":
        scan_module = "auxiliary/scanner/smb/smb_ms17_010"
    else:
        return f"Unknown scan type: {scan_type}. Available types: ping, port, service, vuln"
    
    # Prepare the command
    cmd_parts = [
        f"use {scan_module}",
        f"set RHOSTS {target}"
    ]
    
    # Add any additional options
    if options:
        option_pairs = options.split()
        for pair in option_pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                cmd_parts.append(f"set {key} {value}")
    
    cmd_parts.append("run")
    command = "; ".join(cmd_parts)
    
    # Run the command
    result = await msf_service.run_command(command, ctx)
    
    if result["success"]:
        return f"Scan results for {target} using {scan_module}:\n\n{result['stdout']}"
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Failed to run scan: {error_msg}"

# MCP Tool: Database management
@mcp.tool()
async def manage_database(ctx: Context = None, command: str = "status") -> str:
    """
    Manage the Metasploit database.
    
    Args:
        command: Database command (status, hosts, services, vulns, creds, loot, notes)
    
    Returns:
        Result of the database operation
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    valid_commands = ["status", "hosts", "services", "vulns", "creds", "loot", "notes"]
    if command not in valid_commands:
        return f"Invalid database command. Valid commands: {', '.join(valid_commands)}"
    
    # Map command to MSF command
    msf_command = ""
    if command == "status":
        msf_command = "db_status"
    elif command == "hosts":
        msf_command = "hosts"
    elif command == "services":
        msf_command = "services"
    elif command == "vulns":
        msf_command = "vulns"
    elif command == "creds":
        msf_command = "creds"
    elif command == "loot":
        msf_command = "loot"
    elif command == "notes":
        msf_command = "notes"
    
    # Run the command
    result = await msf_service.run_command(msf_command, ctx)
    
    if result["success"]:
        output = f"Database {command} command results:\n\n{result['stdout']}"
        
        # Add parsed results if available
        if command == "hosts" and "hosts" in result:
            output += f"\n\nParsed hosts:\n{json.dumps(result['hosts'], indent=2)}"
        elif command == "services" and "services" in result:
            output += f"\n\nParsed services:\n{json.dumps(result['services'], indent=2)}"
        elif command == "vulns" and "vulnerabilities" in result:
            output += f"\n\nParsed vulnerabilities:\n{json.dumps(result['vulnerabilities'], indent=2)}"
        
        return output
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Failed to execute database command: {error_msg}"


# MCP Tool: Session management
@mcp.tool()
async def manage_sessions(ctx: Context = None, command: str = "list", session_id: str = "") -> str:
    """
    List and manage Metasploit sessions.
    
    Args:
        command: Session command (list, interact, kill)
        session_id: ID of the session for interact/kill commands
    
    Returns:
        Result of the session operation
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    valid_commands = ["list", "interact", "kill"]
    if command not in valid_commands:
        return f"Invalid session command. Valid commands: {', '.join(valid_commands)}"
    
    # Map command to MSF command
    msf_command = ""
    if command == "list":
        msf_command = "sessions -l"
    elif command == "interact" and session_id:
        msf_command = f"sessions -i {session_id}"
    elif command == "kill" and session_id:
        msf_command = f"sessions -k {session_id}"
    else:
        return "Invalid command or missing session ID."
    
    # Run the command
    result = await msf_service.run_command(msf_command, ctx)
    
    if result["success"]:
        if command == "list":
            if "sessions" in result:
                output = f"Active sessions:\n\n{result['stdout']}\n\n"
                output += f"Parsed sessions:\n{json.dumps(result['sessions'], indent=2)}"
                return output
            else:
                return f"Active sessions:\n\n{result['stdout']}"
        elif command == "interact":
            return f"Session {session_id} interaction:\n\n{result['stdout']}"
        elif command == "kill":
            return f"Session {session_id} killed:\n\n{result['stdout']}"
    else:
        error_msg = result.get("error", "Unknown error")
        return f"Failed to {command} session: {error_msg}"


# MCP Tool: Generate payload with msfvenom
@mcp.tool()
async def generate_payload(ctx: Context = None, payload: str = "", options: str = "") -> str:
    """
    Generate a payload using msfvenom.
    
    Args:
        payload: Payload type (e.g., 'windows/meterpreter/reverse_tcp')
        options: Additional options (e.g., 'LHOST=192.168.1.1 LPORT=4444 -f exe')
    
    Returns:
        Generated payload or command output
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    if not payload:
        return "Please provide a payload type."
    
    # Prepare the msfvenom command parameters
    params = ["-p", payload]
    
    # Add any additional options
    if options:
        option_parts = shlex.split(options)
        params.extend(option_parts)
    
    # Run msfvenom
    result = await msf_service.run_msfvenom(params, ctx)
    
    if result["success"]:
        output = f"Payload generation successful:\n\n"
        output += result["stdout"]
        
        if result["stderr"]:
            output += f"\nWarnings/Info:\n{result['stderr']}"
            
        return output
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to generate payload: {error_msg}"


# MCP Tool: Show module information
@mcp.tool()
async def show_module_info(ctx: Context = None, module_path: str = "") -> str:
    """
    Show detailed information about a Metasploit module.
    
    Args:
        module_path: Full path to the module (e.g., 'exploit/windows/smb/ms17_010_eternalblue')
    
    Returns:
        Module information
    """
    # Check if Metasploit is installed
    if not await check_metasploit_installed(ctx):
        return "Metasploit Framework not found. Please ensure it is installed."
    
    if not module_path:
        return "Please provide a module path."
    
    # Validate module path
    if msf_service._validate_command(f"use {module_path}"):
        # Build command
        command = f"use {module_path}; info"
        
        # Run the command
        result = await msf_service.run_command(command, ctx)
        
        if result["success"]:
            return f"Module information for {module_path}:\n\n{result['stdout']}"
        else:
            error_msg = result.get("error", "Unknown error")
            return f"Failed to get module information: {error_msg}"
    else:
        return f"Invalid or disallowed module path: {module_path}"

# MCP Tool: Browse documentation
@mcp.tool()
async def browse_documentation(ctx: Context = None, document_name: str = "") -> str:
    """
    Browse and view documentation files.
    
    Args:
        document_name: Name of the document to view (leave empty to list available docs)
    
    Returns:
        Documentation content or list of available documents
    """
    if ctx:
        await ctx.info(f"Accessing documentation: {document_name if document_name else 'index'}")
    
    # If no specific document is requested, list available docs
    if not document_name:
        return list_available_docs()
    
    # If a specific document is requested
    return get_document_content(document_name)

# MCP Tool: List all available commands
@mcp.tool()
async def list_mcp_commands(ctx: Context = None) -> str:
    """
    List all available commands and tools in this MCP.
    
    Returns:
        Formatted list of commands with descriptions
    """
    if ctx:
        await ctx.info("Listing available commands")
        
    return list_commands()

# Main function to run the server
if __name__ == "__main__":
    # Display MCP SDK and environment information
    logger.info(f"Starting Metasploit Framework Console MCP v{VERSION}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"MCP SDK version: {MCP_VERSION}")
    logger.info(f"Package versions: {package_versions}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
    
    # Check if msfconsole is available
    if not os.path.exists(CONFIG["metasploit"]["msfconsole_path"]):
        logger.warning(f"msfconsole not found at {CONFIG['metasploit']['msfconsole_path']}")
        print(f"Warning: msfconsole not found at {CONFIG['metasploit']['msfconsole_path']}")
        print("Some functionality may be limited without Metasploit Framework installed.")
        
        # Try to find msfconsole in PATH
        msf_path = shutil.which("msfconsole")
        if msf_path:
            logger.info(f"Found msfconsole in PATH at {msf_path}")
            print(f"Found msfconsole in PATH at {msf_path}")
            CONFIG["metasploit"]["msfconsole_path"] = msf_path
    
    # Print configuration information
    print(f"Starting Metasploit Console MCP server v{VERSION}")
    print(f"MCP SDK version: {MCP_VERSION}")
    print(f"Using msfconsole at: {CONFIG['metasploit']['msfconsole_path']}")
    print(f"Using msfvenom at: {CONFIG['metasploit']['msfvenom_path']}")
    print(f"Current workspace: {CONFIG['metasploit']['workspace']}")
    
    try:
        # Run the server
        print("Running MCP server...")
        mcp.run(transport="stdio")
    except KeyboardInterrupt:
        print("\nShutting down Metasploit Console MCP server...")
        logger.info("Server stopped by keyboard interrupt")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        print(f"Error: {e}")
        # Print traceback for easier debugging
        import traceback
        traceback.print_exc()
        sys.exit(1)
