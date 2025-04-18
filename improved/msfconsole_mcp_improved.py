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
import re
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
MSF_BIN_PATH = "/usr/bin"
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

    async def execute_command(self, command: str, timeout: int = None) -> str:
        """Execute a command in the Metasploit console and return the result."""
        if not self.running:
            raise RuntimeError("Metasploit console is not running")
        
        # Use specified timeout or default
        timeout = timeout or self.command_timeout
        
        # Queue the command
        await self.command_queue.put(command)
        
        try:
            # Wait for result with timeout
            result = await asyncio.wait_for(self.result_queue.get(), timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Command timed out after {timeout} seconds: {command}")
            raise TimeoutError(f"Command execution timed out: {command}")

    async def stop(self):
        """Stop the Metasploit console process."""
        if self.process and self.process.returncode is None:
            logger.info("Stopping Metasploit console process...")
            try:
                # Try to exit gracefully
                await self.execute_command("exit", timeout=5)
            except Exception:
                pass
            
            # Terminate if still running
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), 5)
            except (asyncio.TimeoutError, ProcessLookupError):
                logger.warning("Force killing Metasploit console process")
                self.process.kill()
            
        self.running = False
        logger.info("Metasploit console stopped")

    async def _process_stdout(self):
        """Process stdout from the Metasploit console."""
        buffer = ""
        prompt_pattern = r"\s*msf\w*\s*>\s*$"
        
        while self.running and self.process and not self.process.stdout.at_eof():
            try:
                # Read a chunk of data
                data = await self.process.stdout.read(1024)
                if not data:
                    break
                
                # Decode and add to buffer
                buffer += data.decode("utf-8", errors="replace")
                
                # Check for command prompt
                if re.search(prompt_pattern, buffer, re.MULTILINE):
                    # We have a complete command result
                    result = buffer.strip()
                    buffer = ""
                    
                    # Put result in queue if we're waiting for one
                    if not self.result_queue.empty():
                        await self.result_queue.put(result)
            except Exception as e:
                logger.error(f"Error processing stdout: {e}")
                break
        
        logger.warning("Stdout processing stopped")

    async def _process_stderr(self):
        """Process stderr from the Metasploit console."""
        while self.running and self.process and not self.process.stderr.at_eof():
            try:
                data = await self.process.stderr.read(1024)
                if not data:
                    break
                
                # Log stderr output
                stderr_text = data.decode("utf-8", errors="replace").strip()
                if stderr_text:
                    logger.warning(f"Metasploit stderr: {stderr_text}")
            except Exception as e:
                logger.error(f"Error processing stderr: {e}")
                break
        
        logger.warning("Stderr processing stopped")

    async def _command_processor(self):
        """Process commands from the queue and send to Metasploit console."""
        while self.running:
            try:
                # Get command from queue
                command = await self.command_queue.get()
                
                # Send command to process
                if self.process and self.process.stdin and not self.process.stdin.is_closing():
                    self.process.stdin.write(f"{command}\n".encode("utf-8"))
                    await self.process.stdin.drain()
                    logger.debug(f"Sent command: {command}")
                else:
                    logger.error("Cannot send command: stdin not available")
                    await self.result_queue.put("ERROR: stdin not available")
                
                # Mark command as done
                self.command_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                # Ensure we don't block waiting for result
                if not self.result_queue.empty():
                    await self.result_queue.put(f"ERROR: {str(e)}")
                await asyncio.sleep(1)  # Prevent tight loop on errors

# Import the MCPServer class from mcp_server.py
from mcp_server import MCPServer

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
