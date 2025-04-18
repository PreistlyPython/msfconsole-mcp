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
logger.setLevel(logging.DEBUG)

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
MSF_BIN_PATH = "/opt/metasploit-framework/bin"
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
    async def _process_stdout(self):
        """Process stdout from Metasploit and parse results."""
        if not self.process or not self.process.stdout:
            return
        
        buffer = ""
        while self.running:
            try:
                data = await self.process.stdout.read(1024)
                if not data:
                    # End of stream
                    if self.running:
                        logger.warning("Metasploit stdout stream closed unexpectedly")
                        self.running = False
                    break
                
                # Decode data and add to buffer
                text = data.decode('utf-8', errors='replace')
                buffer += text
                
                # Look for command prompt as delimiter
                if "msf6 >" in buffer or "msf6 exploit(" in buffer or "msf6 auxiliary(" in buffer:
                    # Extract result (everything before the prompt)
                    parts = buffer.split("msf6", 1)
                    result = parts[0].strip()
                    
                    # Store the result if not empty
                    if result:
                        await self.result_queue.put(result)
                    
                    # Keep the remainder (prompt + anything after) in the buffer
                    buffer = "msf6" + parts[1] if len(parts) > 1 else ""
                
            except Exception as e:
                logger.error(f"Error processing Metasploit stdout: {e}")
                # Pause briefly to avoid tight loop if there's a persistent error
                await asyncio.sleep(0.1)

    async def _process_stderr(self):
        """Process stderr from Metasploit and log errors."""
        if not self.process or not self.process.stderr:
            return
        
        while self.running:
            try:
                data = await self.process.stderr.read(1024)
                if not data:
                    break
                
                # Log stderr output
                text = data.decode('utf-8', errors='replace').strip()
                if text:
                    logger.warning(f"Metasploit stderr: {text}")
            except Exception as e:
                logger.error(f"Error processing Metasploit stderr: {e}")
                await asyncio.sleep(0.1)

    async def _command_processor(self):
        """Process commands from the queue and send to Metasploit."""
        while self.running:
            try:
                command, future = await self.command_queue.get()
                
                if not self.process or not self.process.stdin:
                    future.set_exception(Exception("Metasploit process not running"))
                    self.command_queue.task_done()
                    continue
                
                # Send command to Metasploit
                logger.debug(f"Sending command to Metasploit: {command}")
                self.process.stdin.write(f"{command}\n".encode('utf-8'))
                await self.process.stdin.drain()
                
                # Wait for result
                try:
                    result = await asyncio.wait_for(self.result_queue.get(), timeout=self.command_timeout)
                    future.set_result(result)
                    self.result_queue.task_done()
                except asyncio.TimeoutError:
                    logger.warning(f"Command timed out after {self.command_timeout} seconds: {command}")
                    future.set_exception(TimeoutError(f"Command timed out: {command}"))
                
                self.command_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in command processor: {e}")
                await asyncio.sleep(0.1)

    async def execute_command(self, command: str, timeout: Optional[float] = None) -> str:
        """
        Execute a command in the Metasploit console.
        
        Args:
            command: The command to execute
            timeout: Optional timeout in seconds
            
        Returns:
            The command output as a string
        """
        if not self.running:
            raise RuntimeError("Metasploit process is not running")
        
        # Create a future to get the result
        future = asyncio.Future()
        
        # Set custom timeout for this command if specified
        old_timeout = self.command_timeout
        if timeout:
            self.command_timeout = timeout
        
        try:
            # Queue the command
            await self.command_queue.put((command, future))
            
            # Wait for the result
            result = await future
            return result
        
        finally:
            # Restore original timeout
            if timeout:
                self.command_timeout = old_timeout

    async def stop(self):
        """Stop the Metasploit console process."""
        logger.info("Stopping Metasploit console process...")
        
        self.running = False
        
        if self.process:
            try:
                # Try to exit gracefully first
                if self.process.stdin:
                    self.process.stdin.write(b"exit -y\n")
                    await self.process.stdin.drain()
                
                # Give it a moment to exit
                try:
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force terminate if it doesn't exit
                    logger.warning("Metasploit process did not exit gracefully, terminating...")
                    self.process.terminate()
                    await self.process.wait()
                
                logger.info("Metasploit console stopped")
            
            except Exception as e:
                logger.error(f"Error stopping Metasploit console: {e}")
                # Make sure it's terminated
                try:
                    self.process.kill()
                except:
                    pass
class MCPServer:
    """
    Implements a Model Context Protocol server for Metasploit Framework.
    """
    def __init__(self):
        self.msf = MetasploitProcess()
        self.initialized = False
        self.next_id = 1
        self.mcp_version = MCP_VERSION
        self.server_info = {
            "name": "msfconsole-improved",
            "version": "1.0.0",
            "vendor": "Metasploit",
        }
        self.capabilities = {
            "tools": True,
            "resources": False,
            "prompts": False,
        }
        self.tools = self._define_tools()

    def _define_tools(self) -> List[Dict[str, Any]]:
        """Define the tools available in this server."""
        return [
            {
                "name": "get_msf_version",
                "description": "Get the installed Metasploit Framework version.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "title": "get_msf_versionArguments"
                }
            },
            {
                "name": "run_msf_command",
                "description": "Execute a command in msfconsole.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "default": "",
                            "title": "Command"
                        }
                    },
                    "title": "run_msf_commandArguments"
                }
            },
            {
                "name": "search_modules",
                "description": "Search for modules in the Metasploit Framework.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "default": "",
                            "title": "Query"
                        }
                    },
                    "title": "search_modulesArguments"
                }
            },
            {
                "name": "manage_workspaces",
                "description": "List and manage Metasploit workspaces.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "default": "list",
                            "title": "Command"
                        },
                        "workspace_name": {
                            "type": "string",
                            "default": "",
                            "title": "Workspace Name"
                        }
                    },
                    "title": "manage_workspacesArguments"
                }
            },
            {
                "name": "run_scan",
                "description": "Run a scan against target hosts.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scan_type": {
                            "type": "string",
                            "default": "ping",
                            "title": "Scan Type"
                        },
                        "target": {
                            "type": "string",
                            "default": "",
                            "title": "Target"
                        },
                        "options": {
                            "type": "string",
                            "default": "",
                            "title": "Options"
                        }
                    },
                    "title": "run_scanArguments"
                }
            },
            {
                "name": "manage_database",
                "description": "Manage the Metasploit database.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "default": "status",
                            "title": "Command"
                        }
                    },
                    "title": "manage_databaseArguments"
                }
            },
            {
                "name": "manage_sessions",
                "description": "List and manage Metasploit sessions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "default": "list",
                            "title": "Command"
                        },
                        "session_id": {
                            "type": "string",
                            "default": "",
                            "title": "Session Id"
                        }
                    },
                    "title": "manage_sessionsArguments"
                }
            },
            {
                "name": "generate_payload",
                "description": "Generate a payload using msfvenom.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "string",
                            "default": "",
                            "title": "Payload"
                        },
                        "options": {
                            "type": "string",
                            "default": "",
                            "title": "Options"
                        }
                    },
                    "title": "generate_payloadArguments"
                }
            },
            {
                "name": "show_module_info",
                "description": "Show detailed information about a Metasploit module.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "module_path": {
                            "type": "string",
                            "default": "",
                            "title": "Module Path"
                        }
                    },
                    "title": "show_module_infoArguments"
                }
            },
            {
                "name": "browse_documentation",
                "description": "Browse and view documentation files.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_name": {
                            "type": "string",
                            "default": "",
                            "title": "Document Name"
                        }
                    },
                    "title": "browse_documentationArguments"
                }
            },
            {
                "name": "list_mcp_commands",
                "description": "List all available commands and tools in this MCP.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "title": "list_mcp_commandsArguments"
                }
            }
        ]

    async def start(self):
        """Start the MCP server and initialize the Metasploit process."""
        logger.info("Starting MCP server for Metasploit...")
        await self.msf.start()
        
        # Wait for initial command prompt
        await asyncio.sleep(1)
        
        # Ready to receive JSON-RPC messages
        logger.info("MCP server started and ready")
        await self._message_loop()

    async def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping MCP server...")
        await self.msf.stop()
        logger.info("MCP server stopped")

    async def _message_loop(self):
        """Process incoming JSON-RPC messages."""
        while True:
            try:
                # Read line from stdin
                line = await self._read_line()
                if not line:
                    logger.info("End of input stream, stopping server")
                    break
                
                # Parse JSON-RPC message
                try:
                    message = json.loads(line)
                    await self._handle_message(message)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON-RPC message: {e}")
                    await self._send_error(None, ErrorCode.PARSE_ERROR, "Invalid JSON received")
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                # If not recoverable, exit
                if isinstance(e, KeyboardInterrupt) or isinstance(e, asyncio.CancelledError):
                    break
                # Otherwise continue processing messages
                await asyncio.sleep(0.1)
    async def _read_line(self) -> Optional[str]:
        """Read a line from stdin asynchronously."""
        # Create a future to hold the result
        future = asyncio.Future()
        
        # Use run_in_executor to read from stdin in a non-blocking way
        def _read_stdin():
            try:
                return sys.stdin.readline()
            except (EOFError, KeyboardInterrupt):
                return None
        
        # Run the blocking read operation in a thread pool
        line = await asyncio.get_event_loop().run_in_executor(None, _read_stdin)
        
        if not line:
            return None
        
        return line.strip()

    async def _handle_message(self, message: Dict[str, Any]):
        """Handle incoming JSON-RPC messages."""
        if not isinstance(message, dict):
            logger.error(f"Received non-object message: {message}")
            await self._send_error(None, ErrorCode.INVALID_REQUEST, "Message must be a JSON object")
            return
        
        if "jsonrpc" not in message or message["jsonrpc"] != JSONRPC_VERSION:
            logger.error(f"Invalid JSON-RPC version: {message.get('jsonrpc', 'none')}")
            await self._send_error(None, ErrorCode.INVALID_REQUEST, "Invalid JSON-RPC version")
            return
        
        # Request message (has method and id)
        if "method" in message and "id" in message:
            await self._handle_request(message)
        
        # Notification message (has method but no id)
        elif "method" in message and "id" not in message:
            await self._handle_notification(message)
        
        # Response message (has result or error and id)
        elif ("result" in message or "error" in message) and "id" in message:
            logger.warning(f"Received unexpected response message: {message}")
            # This server doesn't expect responses, so log but don't process
        
        else:
            logger.error(f"Invalid JSON-RPC message format: {message}")
            await self._send_error(
                message.get("id"), 
                ErrorCode.INVALID_REQUEST, 
                "Invalid JSON-RPC message format"
            )

    async def _handle_request(self, request: Dict[str, Any]):
        """Handle JSON-RPC request messages."""
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.debug(f"Handling request: method={method}, id={request_id}")
        
        # Handle lifecycle methods
        if method == "initialize":
            await self._handle_initialize(request_id, params)
            return
        
        # Only process tool invocations after initialization
        if not self.initialized:
            await self._send_error(
                request_id,
                ErrorCode.INVALID_REQUEST,
                "Server not initialized, send initialize request first"
            )
            return
        
        # Handle tool invocations
        if method == "tools/invoke":
            await self._handle_tool_invoke(request_id, params)
            return
        
        # Unknown method
        logger.warning(f"Unknown method requested: {method}")
        await self._send_error(
            request_id,
            ErrorCode.METHOD_NOT_FOUND,
            f"Method not found: {method}"
        )

    async def _handle_notification(self, notification: Dict[str, Any]):
    """Handle JSON-RPC notification messages."""
    method = notification.get("method", "")
    params = notification.get("params", {})
    
    logger.debug(f"Handling notification: method={method}, params={params}")
    
    if method == "initialized":
        self.initialized = True
        logger.info("Client sent initialized notification, server ready")
        
        # Send a log message to confirm we received the notification
        await self._send_log("info", "Server successfully initialized")
        return
    
    if method == "$/cancelRequest":
        # Implement request cancellation (optional)
        logger.info(f"Cancellation requested for: {params.get('id')}")
        return
    
    logger.debug(f"Ignoring unknown notification: {method}")

async def _send_log(self, level: str, message: str):
    """Send a log message to the client."""
    log_notification = {
        "jsonrpc": JSONRPC_VERSION,
        "method": "notifications/log",
        "params": {
            "level": level,
            "message": message
        }
    }
    await self._send_json(log_notification)
    logger.debug(f"Sent log notification: {level} - {message}")


    async def _handle_initialize(self, request_id: Union[str, int], params: Dict[str, Any]):
        """Handle the initialize request."""
        client_info = params.get("clientInfo", {})
        client_name = client_info.get("name", "unknown")
        client_version = client_info.get("version", "unknown")
        
        logger.info(f"Initialization request from client: {client_name} {client_version}")
        
        # Build initialization response
        response = {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,
            "result": {
                "serverInfo": self.server_info,
                "protocolVersion": self.mcp_version,
                "capabilities": self.capabilities,
                "tools": self.tools if self.capabilities["tools"] else None,
                "resources": None,  # Not implemented
                "prompts": None,    # Not implemented
            }
        }
        
        await self._send_json(response)
        logger.info("Initialization response sent")

    async def _handle_tool_invoke(self, request_id: Union[str, int], params: Dict[str, Any]):
        """Handle tool invocation requests."""
        tool_name = params.get("name", "")
        tool_params = params.get("parameters", {})
        
        logger.info(f"Tool invocation request: {tool_name}")
        
        # Implement tool handler dispatch
        try:
            if tool_name == "get_msf_version":
                result = await self._tool_get_msf_version()
            elif tool_name == "run_msf_command":
                result = await self._tool_run_msf_command(tool_params.get("command", ""))
            elif tool_name == "search_modules":
                result = await self._tool_search_modules(tool_params.get("query", ""))
            elif tool_name == "manage_workspaces":
                result = await self._tool_manage_workspaces(
                    tool_params.get("command", "list"),
                    tool_params.get("workspace_name", "")
                )
            elif tool_name == "run_scan":
                result = await self._tool_run_scan(
                    tool_params.get("scan_type", "ping"),
                    tool_params.get("target", ""),
                    tool_params.get("options", "")
                )
            elif tool_name == "manage_database":
                result = await self._tool_manage_database(tool_params.get("command", "status"))
            elif tool_name == "manage_sessions":
                result = await self._tool_manage_sessions(
                    tool_params.get("command", "list"),
                    tool_params.get("session_id", "")
                )
            elif tool_name == "generate_payload":
                result = await self._tool_generate_payload(
                    tool_params.get("payload", ""),
                    tool_params.get("options", "")
                )
            elif tool_name == "show_module_info":
                result = await self._tool_show_module_info(tool_params.get("module_path", ""))
            elif tool_name == "browse_documentation":
                result = await self._tool_browse_documentation(tool_params.get("document_name", ""))
            elif tool_name == "list_mcp_commands":
                result = await self._tool_list_mcp_commands()
            else:
                await self._send_error(
                    request_id,
                    ErrorCode.METHOD_NOT_FOUND,
                    f"Tool not found: {tool_name}"
                )
                return
            
            # Send success response
            response = {
                "jsonrpc": JSONRPC_VERSION,
                "id": request_id,
                "result": result
            }
            await self._send_json(response)
            
        except Exception as e:
            logger.error(f"Error handling tool invocation: {e}")
            await self._send_error(
                request_id,
                ErrorCode.INTERNAL_ERROR,
                f"Error executing tool: {str(e)}"
            )
    async def _send_json(self, data: Dict[str, Any]):
    """Send a JSON response to stdout."""
    try:
        # Add newline to ensure proper message separation
        json_str = json.dumps(data) + "
"
        logger.debug(f"Sending JSON response (first 100 chars): {json_str[:100]}...")
        # In MCP, we must ensure only valid JSON is sent to stdout
        sys.stdout.write(json_str)
        sys.stdout.flush()
        logger.debug("JSON response sent and flushed")
    except Exception as e:
        logger.error(f"Error sending JSON response: {e}")
        logger.error(f"Response data: {str(data)[:200]}...")


    async def _send_error(self, 
                          request_id: Optional[Union[str, int]], 
                          code: int, 
                          message: str, 
                          data: Any = None):
        """Send a JSON-RPC error response."""
        error_response = {
            "jsonrpc": JSONRPC_VERSION,
            "id": request_id,  # Can be null for parse errors
            "error": {
                "code": code,
                "message": message
            }
        }
        
        if data is not None:
            error_response["error"]["data"] = data
            
        await self._send_json(error_response)

    # Tool implementations
    async def _tool_get_msf_version(self) -> Dict[str, Any]:
        """Get the Metasploit Framework version information."""
        try:
            output = await self.msf.execute_command("version")
            return {
                "version": output.strip()
            }
        except Exception as e:
            logger.error(f"Error getting MSF version: {e}")
            raise

    async def _tool_run_msf_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in the Metasploit console."""
        if not command:
            return {"output": "No command specified"}
        
        try:
            output = await self.msf.execute_command(command)
            return {
                "command": command,
                "output": output
            }
        except Exception as e:
            logger.error(f"Error executing MSF command: {e}")
            raise

    async def _tool_search_modules(self, query: str) -> Dict[str, Any]:
        """Search for modules in the Metasploit Framework."""
        if not query:
            return {"modules": [], "message": "No search query specified"}
        
        try:
            output = await self.msf.execute_command(f"search {query}")
            
            # Parse the module list
            modules = []
            lines = output.split('\n')
            
            # Skip header lines and empty lines
            for line in lines:
                if not line.strip() or "Matching Modules" in line:
                    continue
                
                # Basic parsing of module information
                modules.append(line.strip())
            
            return {
                "query": query,
                "modules": modules,
                "raw_output": output
            }
        except Exception as e:
            logger.error(f"Error searching modules: {e}")
            raise

    async def _tool_manage_workspaces(self, command: str, workspace_name: str) -> Dict[str, Any]:
        """Manage Metasploit workspaces."""
        try:
            msf_command = "workspace"
            
            if command == "list":
                msf_command = "workspace -v"
            elif command == "add" and workspace_name:
                msf_command = f"workspace -a {workspace_name}"
            elif command == "delete" and workspace_name:
                msf_command = f"workspace -d {workspace_name}"
            elif command == "select" and workspace_name:
                msf_command = f"workspace {workspace_name}"
            else:
                return {"error": "Invalid workspace command or missing workspace name"}
            
            output = await self.msf.execute_command(msf_command)
            
            return {
                "command": command,
                "workspace_name": workspace_name if workspace_name else None,
                "output": output
            }
        except Exception as e:
            logger.error(f"Error managing workspaces: {e}")
            raise

    async def _tool_run_scan(self, scan_type: str, target: str, options: str) -> Dict[str, Any]:
        """Run a scan against target hosts."""
        if not target:
            return {"error": "No target specified"}
        
        try:
            commands = []
            outputs = []
            
            if scan_type == "ping":
                # Simple ping scan
                command = f"db_nmap -sn {target}"
                if options:
                    command += f" {options}"
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == "port":
                # TCP port scan
                command = f"db_nmap -sS {target}"
                if options:
                    command += f" {options}"
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == "service":
                # Service detection scan
                command = f"db_nmap -sS -sV {target}"
                if options:
                    command += f" {options}"
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
                
            elif scan_type == "vuln":
                # Vulnerability scan
                command = f"db_nmap -sS -sV --script vuln {target}"
                if options:
                    command += f" {options}"
                
                commands.append(command)
                outputs.append(await self.msf.execute_command(command))
            
            else:
                return {"error": f"Unknown scan type: {scan_type}"}
            
            # Get scan results from database
            commands.append("hosts")
            outputs.append(await self.msf.execute_command("hosts"))
            
            commands.append("services")
            outputs.append(await self.msf.execute_command("services"))
            
            return {
                "scan_type": scan_type,
                "target": target,
                "options": options if options else None,
                "commands": commands,
                "raw_output": outputs
            }
        except Exception as e:
            logger.error(f"Error running scan: {e}")
            raise
    async def _tool_manage_database(self, command: str) -> Dict[str, Any]:
        """Manage the Metasploit database."""
        try:
            msf_command = command
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
            else:
                return {"error": f"Unknown database command: {command}"}
            
            output = await self.msf.execute_command(msf_command)
            
            return {
                "command": command,
                "output": output
            }
        except Exception as e:
            logger.error(f"Error managing database: {e}")
            raise

    async def _tool_manage_sessions(self, command: str, session_id: str) -> Dict[str, Any]:
        """List and manage Metasploit sessions."""
        try:
            msf_command = "sessions"
            
            if command == "list":
                msf_command = "sessions -v"
            elif command == "interact" and session_id:
                # For interactive sessions, this will be more complex
                # We'll just provide information since we can't truly interact via MCP
                return {
                    "command": command,
                    "session_id": session_id,
                    "message": "Interactive sessions are not supported via MCP. Use 'list' to view sessions."
                }
            elif command == "kill" and session_id:
                msf_command = f"sessions -k {session_id}"
            else:
                return {"error": "Invalid session command or missing session ID"}
            
            output = await self.msf.execute_command(msf_command)
            
            return {
                "command": command,
                "session_id": session_id if session_id else None,
                "output": output
            }
        except Exception as e:
            logger.error(f"Error managing sessions: {e}")
            raise

    async def _tool_generate_payload(self, payload: str, options: str) -> Dict[str, Any]:
        """Generate a payload using msfvenom."""
        if not payload:
            return {"error": "No payload specified"}
        
        try:
            # Using msfvenom via the MSF console
            command = f"use payload/{payload}"
            await self.msf.execute_command(command)
            
            # Set options and generate
            if options:
                option_pairs = options.split()
                for option in option_pairs:
                    if "=" in option:
                        key, value = option.split("=", 1)
                        await self.msf.execute_command(f"set {key} {value}")
            
            # Generate the payload
            output = await self.msf.execute_command("generate")
            
            return {
                "payload": payload,
                "options": options if options else None,
                "output": output
            }
        except Exception as e:
            logger.error(f"Error generating payload: {e}")
            raise

    async def _tool_show_module_info(self, module_path: str) -> Dict[str, Any]:
        """Show detailed information about a Metasploit module."""
        if not module_path:
            return {"error": "No module path specified"}
        
        try:
            # Use the module
            use_output = await self.msf.execute_command(f"use {module_path}")
            
            # Get info
            info_output = await self.msf.execute_command("info")
            
            # Get options
            options_output = await self.msf.execute_command("options")
            
            return {
                "module_path": module_path,
                "info": info_output,
                "options": options_output
            }
        except Exception as e:
            logger.error(f"Error showing module info: {e}")
            raise

    async def _tool_browse_documentation(self, document_name: str) -> Dict[str, Any]:
        """Browse and view documentation files."""
        try:
            if not document_name:
                # List available documentation
                output = await self.msf.execute_command("help")
                return {
                    "available_docs": output.split("\n")
                }
            else:
                # View specific documentation
                output = await self.msf.execute_command(f"help {document_name}")
                return {
                    "document_name": document_name,
                    "content": output
                }
        except Exception as e:
            logger.error(f"Error browsing documentation: {e}")
            raise

    async def _tool_list_mcp_commands(self) -> Dict[str, Any]:
        """List all available commands and tools in this MCP."""
        try:
            tool_list = [{
                "name": tool["name"],
                "description": tool["description"]
            } for tool in self.tools]
            
            return {
                "tools": tool_list,
                "server_info": self.server_info
            }
        except Exception as e:
            logger.error(f"Error listing MCP commands: {e}")
            raise

# Main entry point
async def main():
    try:
        # Log startup information (to stderr or log file only, not stdout)
        logger.info("Starting Improved Metasploit MCP...")
        logger.info(f"JSON stdout mode: {json_stdout}")
        logger.info(f"Strict mode: {strict_mode}")
        
        # Create and start the server
        server = MCPServer()
        await server.start()
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Install JSON filter if enabled
        if json_stdout or strict_mode:
            try:
                from json_filter import install_json_filter
                json_filter = install_json_filter(debug=True, strict=strict_mode)
                logger.info(f"JSON filtering enabled for stdout (strict mode: {strict_mode})")
            except ImportError as e:
                logger.warning(f"Could not import json_filter module: {e}")
                logger.warning("JSON filtering disabled - protocol errors may occur")
        
        # Run the main async function
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        sys.exit(1)
