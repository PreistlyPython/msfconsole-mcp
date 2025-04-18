#!/usr/bin/env python3

"""
MCP Server for Metasploit Framework
-----------------------------------
This module implements the MCP server for Metasploit Framework integration.
"""

import os
import sys
import logging
import json
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union

# Get logger
logger = logging.getLogger("msfconsole_mcp")

class MCPServer:
    """
    Model Context Protocol (MCP) Server for Metasploit Framework.
    Handles JSON-RPC communication and tool implementations.
    """
    
    def __init__(self):
        """Initialize the MCP server."""
        self.tools = []
        self.server_info = {
            "name": "Metasploit Framework MCP",
            "version": "2.0.0",
            "protocol_version": "2025-03-26"
        }
        # Initialize tools
        self._initialize_tools()
        
    def _initialize_tools(self):
        """Register available tools with the server."""
        self.tools = [
            {
                "name": "get_msf_version",
                "description": "Get the installed Metasploit Framework version.",
                "method": self._tool_get_version
            },
            {
                "name": "run_msf_command",
                "description": "Execute a command in msfconsole.",
                "method": self._tool_run_command
            },
            {
                "name": "search_modules",
                "description": "Search for modules in the Metasploit Framework.",
                "method": self._tool_search_modules
            },
            {
                "name": "manage_workspaces",
                "description": "List and manage Metasploit workspaces.",
                "method": self._tool_manage_workspaces
            },
            {
                "name": "run_scan",
                "description": "Run a scan against target hosts.",
                "method": self._tool_run_scan
            },
            {
                "name": "manage_database",
                "description": "Manage the Metasploit database.",
                "method": self._tool_manage_database
            },
            {
                "name": "manage_sessions",
                "description": "List and manage Metasploit sessions.",
                "method": self._tool_manage_sessions
            },
            {
                "name": "generate_payload",
                "description": "Generate a payload using msfvenom.",
                "method": self._tool_generate_payload
            },
            {
                "name": "show_module_info",
                "description": "Show detailed information about a Metasploit module.",
                "method": self._tool_show_module_info
            },
            {
                "name": "browse_documentation",
                "description": "Browse and view documentation files.",
                "method": self._tool_browse_documentation
            },
            {
                "name": "list_mcp_commands",
                "description": "List all available commands and tools in this MCP.",
                "method": self._tool_list_mcp_commands
            }
        ]
        logger.info(f"Initialized {len(self.tools)} tools")
    
    async def start(self):
        """Start the MCP server."""
        # Initialize the Metasploit process
        from msfconsole_mcp_improved import MetasploitProcess
        self.msf = MetasploitProcess()
        await self.msf.start()
        
        # Start processing JSON-RPC requests
        await self._process_requests()
    
    async def _process_requests(self):
        """Process incoming JSON-RPC requests."""
        logger.info("MCP server ready to process requests")
        
        while True:
            try:
                # Read a line from stdin
                line = await asyncio.to_thread(sys.stdin.readline)
                
                # Check for EOF
                if not line:
                    logger.info("Received EOF, shutting down")
                    break
                
                # Parse as JSON-RPC
                try:
                    request = json.loads(line)
                    await self._handle_request(request)
                except json.JSONDecodeError:
                    logger.warning(f"Received invalid JSON: {line}")
                    self._send_error(None, -32700, "Parse error", "Invalid JSON was received")
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                self._send_error(None, -32603, "Internal error", str(e))
    
    async def _handle_request(self, request: Dict[str, Any]):
        """Handle a JSON-RPC request."""
        # Validate request
        if not isinstance(request, dict) or "method" not in request:
            self._send_error(request.get("id"), -32600, "Invalid request", "Request must be an object with a method field")
            return
        
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        logger.info(f"Received request: method={method}, id={request_id}")
        
        # Handle system methods
        if method == "initialize":
            self._handle_initialize(request_id, params)
            return
        elif method == "shutdown":
            self._handle_shutdown(request_id, params)
            return
        
        # Find and execute the tool
        tool = next((t for t in self.tools if t["name"] == method), None)
        if tool is None:
            self._send_error(request_id, -32601, "Method not found", f"Method '{method}' not found")
            return
        
        try:
            # Call the tool method with params
            result = await tool["method"](**params)
            self._send_result(request_id, result)
        except Exception as e:
            logger.error(f"Error executing tool {method}: {e}")
            self._send_error(request_id, -32603, "Internal error", str(e))
    
    def _handle_initialize(self, request_id: Any, params: Dict[str, Any]):
        """Handle the initialize method."""
        protocol_version = params.get("protocolVersion")
        logger.info(f"Client requested initialization with protocol version: {protocol_version}")
        
        # Return server capabilities
        capabilities = {
            "protocolVersion": self.server_info["protocol_version"],
            "serverInfo": self.server_info,
            "tools": [
                {
                    "name": tool["name"],
                    "description": tool["description"]
                }
                for tool in self.tools
            ]
        }
        
        self._send_result(request_id, capabilities)
    
    def _handle_shutdown(self, request_id: Any, params: Dict[str, Any]):
        """Handle the shutdown method."""
        logger.info("Client requested shutdown")
        self._send_result(request_id, {"success": True})
        # Exit after sending response
        sys.exit(0)
    
    def _send_result(self, request_id: Any, result: Any):
        """Send a successful JSON-RPC response."""
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        print(json.dumps(response), flush=True)
    
    def _send_error(self, request_id: Any, code: int, message: str, data: Any = None):
        """Send a JSON-RPC error response."""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
            
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }
        print(json.dumps(response), flush=True)
    
    # Tool implementations
    async def _tool_get_version(self) -> Dict[str, Any]:
        """Get the installed Metasploit Framework version."""
        try:
            output = await self.msf.execute_command('version')
            
            # Parse version information
            lines = output.split('\n')
            version_info = {
                'version': next((l for l in lines if 'Framework' in l), '').strip(),
                'ruby_version': next((l for l in lines if 'Ruby' in l), '').strip(),
                'platform': next((l for l in lines if 'Platform' in l), '').strip(),
            }
            
            return {
                'version_info': version_info,
                'raw_output': output
            }
        except Exception as e:
            logger.error(f'Error getting MSF version: {e}')
            raise
    
    async def _tool_run_command(self, command: str) -> Dict[str, Any]:
        """Execute a command in msfconsole."""
        if not command:
            return {'error': 'No command specified'}
        
        try:
            output = await self.msf.execute_command(command)
            
            return {
                'command': command,
                'output': output
            }
        except Exception as e:
            logger.error(f'Error running command: {e}')
            raise
    
    async def _tool_search_modules(self, query: str) -> Dict[str, Any]:
        """Search for modules in the Metasploit Framework."""
        if not query:
            return {'error': 'No search query specified'}
        
        try:
            output = await self.msf.execute_command(f'search {query}')
            
            # Parse search results
            modules = []
            lines = output.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#') and not line.startswith('='):
                    # Simple parsing - could be enhanced
                    modules.append(line.strip())
            
            return {
                'query': query,
                'modules': modules,
                'raw_output': output
            }
        except Exception as e:
            logger.error(f'Error searching modules: {e}')
            raise
    
    async def _tool_manage_workspaces(self, command: str, workspace_name: str = '') -> Dict[str, Any]:
        """List and manage Metasploit workspaces."""
        try:
            if command == 'list':
                output = await self.msf.execute_command('workspace')
                workspaces = [line.strip() for line in output.split('\n') if line.strip()]
                return {
                    'workspaces': workspaces,
                    'raw_output': output
                }
            elif command == 'add' and workspace_name:
                output = await self.msf.execute_command(f'workspace -a {workspace_name}')
                return {
                    'action': 'add',
                    'workspace': workspace_name,
                    'output': output
                }
            elif command == 'delete' and workspace_name:
                output = await self.msf.execute_command(f'workspace -d {workspace_name}')
                return {
                    'action': 'delete',
                    'workspace': workspace_name,
                    'output': output
                }
            elif command == 'select' and workspace_name:
                output = await self.msf.execute_command(f'workspace {workspace_name}')
                return {
                    'action': 'select',
                    'workspace': workspace_name,
                    'output': output
                }
            else:
                return {'error': 'Invalid workspace command or missing workspace name'}
        except Exception as e:
            logger.error(f'Error managing workspaces: {e}')
            raise
    
    async def _tool_run_scan(self, scan_type: str, target: str, options: str = '') -> Dict[str, Any]:
        """Run a scan against target hosts."""
        if not target:
            return {'error': 'No target specified'}
        
        try:
            commands = []
            outputs = []
            
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

    async def _tool_manage_sessions(self, command: str, session_id: str = '') -> Dict[str, Any]:
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

    async def _tool_generate_payload(self, payload: str, options: str = '') -> Dict[str, Any]:
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

    async def _tool_browse_documentation(self, document_name: str = '') -> Dict[str, Any]:
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
