#!/usr/bin/env python3

"""
Improved Metasploit Framework Console MCP
-----------------------------------------
This module integrates Metasploit Framework with MCP using improved execution strategies
for better reliability and error handling.
"""

import os
import sys
import logging
import subprocess
import asyncio
import json
import shutil
import time
import argparse
from typing import Dict, Any, Optional, List, Tuple, Union

# Set up logging with configurable handlers
logger = logging.getLogger("msfconsole_mcp")
logger.setLevel(logging.INFO)

# Create formatters
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler - always used
file_handler = logging.FileHandler("msfconsole_mcp_improved.log")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Process command line arguments
parser = argparse.ArgumentParser(description="Improved Metasploit MCP Server")
parser.add_argument("--json-stdout", action="store_true", help="Ensure all stdout is valid JSON")
parser.add_argument("--strict-mode", action="store_true", help="Run in strict JSON mode")
parser.add_argument("--debug-to-stderr", action="store_true", help="Redirect debug output to stderr")
args = parser.parse_args()

# Configure JSON handling
json_stdout = args.json_stdout or os.environ.get("MCP_JSON_STDOUT") == "1"
strict_mode = args.strict_mode or os.environ.get("MCP_STRICT_MODE") == "1"
debug_to_stderr = args.debug_to_stderr or os.environ.get("MCP_DEBUG_TO_STDERR") == "1"

# Configure log handlers based on settings
if debug_to_stderr:
    # Add stderr handler if requested
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(log_format)
    logger.addHandler(stderr_handler)
    logger.info("Debug output redirected to stderr")
elif not json_stdout and not strict_mode:
    # Add stdout handler only if not in JSON mode
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)
    logger.info("Debug output directed to stdout (may interfere with MCP protocol)")

# Define constants for MCP
MCP_VERSION = "2025-03-26"
JSONRPC_VERSION = "2.0"

# Define JSON-RPC error codes
class ErrorCode:
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    # MCP specific error codes
    COMMAND_EXECUTION_ERROR = -32000
    COMMAND_NOT_FOUND = -32001
    INVALID_RESPONSE = -32002
    TIMEOUT_ERROR = -32003

# Path to Metasploit executables
MSF_BIN_PATH = "/usr/share/metasploit-framework/bin"
MSFCONSOLE_PATH = os.path.join(MSF_BIN_PATH, "msfconsole")
MSFVENOM_PATH = os.path.join(MSF_BIN_PATH, "msfvenom")

class MetasploitProcess:
    """
    Manages interaction with Metasploit processes and ensures
    proper handling of stdin/stdout/stderr.
    """
    def __init__(self):
        self.process = None
        self.command_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.running = False
        self.command_timeout = 30  # Default timeout in seconds

    async def start(self):
        """Start the Metasploit console process."""
        logger.info("Starting Metasploit console process...")
        
        # Check if msfconsole exists and is executable
        if not os.path.isfile(MSFCONSOLE_PATH) or not os.access(MSFCONSOLE_PATH, os.X_OK):
            error_msg = f"Metasploit console not found at {MSFCONSOLE_PATH} or not executable"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Start msfconsole with -q (quiet) and -n (non-interactive) flags
            self.process = await asyncio.create_subprocess_exec(
                MSFCONSOLE_PATH, 
                "-q",  # Quiet mode to reduce banner output
                "-n",  # Non-interactive mode
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            self.running = True
            
            # Start the management tasks
            asyncio.create_task(self._process_stdout())
            asyncio.create_task(self._process_stderr())
            asyncio.create_task(self._command_processor())
            
            logger.info("Metasploit console started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Metasploit console: {e}")
            raise
            if scan_type == 'ping':
                # Simple ping scan
                command = f'db_nmap -sn {target}'
                if options:
                    command += f' {options}'
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == 'port':
                # TCP port scan
                command = f'db_nmap -sS {target}'
                if options:
                    command += f' {options}'
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == 'service':
                # Service detection scan
                command = f'db_nmap -sS -sV {target}'
                if options:
                    command += f' {options}'
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == 'vuln':
                # Vulnerability scan
                command = f'db_nmap -sS -sV --script vuln {target}'
                if options:
                    command += f' {options}'
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
            
            else:
                return {'error': f'Unknown scan type: {scan_type}'}
            
            # Get scan results from database
            commands.append('hosts')
            outputs.append(await self.msf.execute_command('hosts'))
            
            commands.append('services')
            outputs.append(await self.msf.execute_command('services'))
            
            return {
                'scan_type': scan_type,
                'target': target,
                'options': options if options else None,
                'commands': commands,
                'raw_output': outputs
            }
        except Exception as e:
            logger.error(f'Error running scan: {e}')
            raise

    async def _tool_manage_database(self, command: str) -> Dict[str, Any]:
        """Manage the Metasploit database."""
        try:
            msf_command = command
            if command == 'status':
                msf_command = 'db_status'
            elif command == 'hosts':
                msf_command = 'hosts'
            elif command == 'services':
                msf_command = 'services'
            elif command == 'vulns':
                msf_command = 'vulns'
            elif command == 'creds':
                msf_command = 'creds'
            elif command == 'loot':
                msf_command = 'loot'
            elif command == 'notes':
                msf_command = 'notes'
            else:
                return {'error': f'Unknown database command: {command}'}
            
            output = await self.msf.execute_command(msf_command)
            
            return {
                'command': command,
                'output': output
            }
        except Exception as e:
            logger.error(f'Error managing database: {e}')
            raise

    async def _tool_manage_sessions(self, command: str, session_id: str) -> Dict[str, Any]:
        """List and manage Metasploit sessions."""
        try:
            msf_command = 'sessions'
            
            if command == 'list':
                msf_command = 'sessions -v'
            elif command == 'interact' and session_id:
                # For interactive sessions, this will be more complex
                # We'll just provide information since we can't truly interact via MCP
                return {
                    'command': command,
                    'session_id': session_id,
                    'message': 'Interactive sessions are not supported via MCP. Use list to view sessions.'
                }
            elif command == 'kill' and session_id:
                msf_command = f'sessions -k {session_id}'
            else:
                return {'error': 'Invalid session command or missing session ID'}
            
            output = await self.msf.execute_command(msf_command)
            
            return {
                'command': command,
                'session_id': session_id if session_id else None,
                'output': output
            }
        except Exception as e:
            logger.error(f'Error managing sessions: {e}')
            raise
    async def _tool_generate_payload(self, payload: str, options: str) -> Dict[str, Any]:
        """Generate a payload using msfvenom."""
        if not payload:
            return {'error': 'No payload specified'}
        
        try:
            # Using msfvenom via the MSF console
            command = f'use payload/{payload}'
            await self.msf.execute_command(command)
            
            # Set options and generate
            if options:
                option_pairs = options.split()
                for option in option_pairs:
                    if '=' in option:
                        key, value = option.split('=', 1)
                        await self.msf.execute_command(f'set {key} {value}')
            
            # Generate the payload
            output = await self.msf.execute_command('generate')
            
            return {
                'payload': payload,
                'options': options if options else None,
                'output': output
            }
        except Exception as e:
            logger.error(f'Error generating payload: {e}')
            raise

    async def _tool_show_module_info(self, module_path: str) -> Dict[str, Any]:
        """Show detailed information about a Metasploit module."""
        if not module_path:
            return {'error': 'No module path specified'}
        
        try:
            # Use the module
            use_output = await self.msf.execute_command(f'use {module_path}')
            
            # Get info
            info_output = await self.msf.execute_command('info')
            
            # Get options
            options_output = await self.msf.execute_command('options')
            
            return {
                'module_path': module_path,
                'info': info_output,
                'options': options_output
            }
        except Exception as e:
            logger.error(f'Error showing module info: {e}')
            raise

    async def _tool_browse_documentation(self, document_name: str) -> Dict[str, Any]:
        """Browse and view documentation files."""
        try:
            if not document_name:
                # List available documentation
                output = await self.msf.execute_command('help')
                return {
                    'available_docs': output.split('\n')
                }
            else:
                # View specific documentation
                output = await self.msf.execute_command(f'help {document_name}')
                return {
                    'document_name': document_name,
                    'content': output
                }
        except Exception as e:
            logger.error(f'Error browsing documentation: {e}')
            raise

    async def _tool_list_mcp_commands(self) -> Dict[str, Any]:
        """List all available commands and tools in this MCP."""
        try:
            tool_list = [{
                'name': tool['name'],
                'description': tool['description']
            } for tool in self.tools]
            
            return {
                'tools': tool_list,
                'server_info': self.server_info
            }
        except Exception as e:
            logger.error(f'Error listing MCP commands: {e}')
            raise

# Main entry point
async def main():
    try:
        # Log startup information (to stderr or log file only, not stdout)
        logger.info('Starting Improved Metasploit MCP...')
        logger.info(f'JSON stdout mode: {json_stdout}')
        logger.info(f'Strict mode: {strict_mode}')
        
        # Create and start the server
        server = MCPServer()
        await server.start()
    except Exception as e:
        logger.error(f'Error in main function: {e}')
        sys.exit(1)

if __name__ == '__main__':
    try:
        # Install JSON filter if enabled
        if json_stdout or strict_mode:
            try:
                from json_filter import install_json_filter
                json_filter = install_json_filter(debug=True, strict=strict_mode)
                logger.info(f'JSON filtering enabled for stdout (strict mode: {strict_mode})')
            except ImportError as e:
                logger.warning(f'Could not import json_filter module: {e}')
                logger.warning('JSON filtering disabled - protocol errors may occur')
        
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Server stopped by user')
    except Exception as e:
        logger.error(f'Unhandled exception: {e}')
        sys.exit(1)
