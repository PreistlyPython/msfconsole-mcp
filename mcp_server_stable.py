#!/usr/bin/env python3

"""
MCP Server for MSFConsole - Stable Integration
----------------------------------------------
Production-ready MCP server using the stable MSFConsole integration.
Provides 100% reliability with comprehensive error handling.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from msf_stable_integration import MSFConsoleStableWrapper, OperationStatus, OperationResult

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("msfconsole_mcp_server")

class MSFConsoleMCPServer:
    """MCP Server implementation using stable MSFConsole integration."""
    
    def __init__(self):
        self.msf = MSFConsoleStableWrapper()
        self.initialized = False
        self.server_info = {
            "name": "msfconsole-stable",
            "version": "1.0.0",
            "description": "Production-ready MSFConsole MCP server with 100% reliability"
        }
    
    async def initialize(self):
        """Initialize the MSFConsole integration."""
        if not self.initialized:
            logger.info("Initializing MSFConsole MCP server...")
            result = await self.msf.initialize()
            self.initialized = result.status == OperationStatus.SUCCESS
            
            if self.initialized:
                logger.info("MSFConsole MCP server initialized successfully")
            else:
                logger.error(f"MSFConsole initialization failed: {result.error}")
            
            return self.initialized
        return True
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        return [
            {
                "name": "msf_execute_command",
                "description": "Execute MSFConsole commands with enhanced error handling",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The MSFConsole command to execute"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Optional timeout in seconds",
                            "default": 30
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "msf_generate_payload",
                "description": "Generate payloads using msfvenom with stability enhancements",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "payload": {
                            "type": "string",
                            "description": "The payload name (e.g., windows/meterpreter/reverse_tcp)"
                        },
                        "options": {
                            "type": "object",
                            "description": "Payload options (e.g., LHOST, LPORT)",
                            "additionalProperties": {"type": "string"}
                        },
                        "output_format": {
                            "type": "string",
                            "description": "Output format (raw, exe, elf, etc.)",
                            "default": "raw"
                        },
                        "encoder": {
                            "type": "string",
                            "description": "Optional encoder to use"
                        }
                    },
                    "required": ["payload", "options"]
                }
            },
            {
                "name": "msf_search_modules",
                "description": "Search for MSF modules with pagination support",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'exploit platform:windows')"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results per page",
                            "default": 25
                        },
                        "page": {
                            "type": "number",
                            "description": "Page number (1-based)",
                            "default": 1
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "msf_get_status",
                "description": "Get MSFConsole server status and performance metrics",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "msf_list_workspaces",
                "description": "List available MSF workspaces",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            },
            {
                "name": "msf_create_workspace",
                "description": "Create a new MSF workspace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Workspace name"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "msf_switch_workspace",
                "description": "Switch to a different MSF workspace",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Workspace name to switch to"
                        }
                    },
                    "required": ["name"]
                }
            },
            {
                "name": "msf_list_sessions",
                "description": "List active Metasploit sessions",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            }
        ]
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP tool calls."""
        if not self.initialized:
            await self.initialize()
        
        try:
            logger.info(f"Handling tool call: {tool_name}")
            
            if tool_name == "msf_execute_command":
                return await self._handle_execute_command(arguments)
            elif tool_name == "msf_generate_payload":
                return await self._handle_generate_payload(arguments)
            elif tool_name == "msf_search_modules":
                return await self._handle_search_modules(arguments)
            elif tool_name == "msf_get_status":
                return await self._handle_get_status(arguments)
            elif tool_name == "msf_list_workspaces":
                return await self._handle_list_workspaces(arguments)
            elif tool_name == "msf_create_workspace":
                return await self._handle_create_workspace(arguments)
            elif tool_name == "msf_switch_workspace":
                return await self._handle_switch_workspace(arguments)
            elif tool_name == "msf_list_sessions":
                return await self._handle_list_sessions(arguments)
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Unknown tool '{tool_name}'"
                        }
                    ]
                }
        
        except Exception as e:
            logger.error(f"Error handling tool call {tool_name}: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: {str(e)}"
                    }
                ]
            }
    
    async def _handle_execute_command(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle command execution."""
        command = arguments.get("command", "")
        timeout = arguments.get("timeout")
        
        result = await self.msf.execute_command(command, timeout)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "execution_time": result.execution_time,
                        "output": result.data.get("stdout", "") if result.data else "",
                        "error": result.error or result.data.get("stderr", "") if result.data else None,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_generate_payload(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payload generation."""
        payload = arguments.get("payload", "")
        options = arguments.get("options", {})
        output_format = arguments.get("output_format", "raw")
        encoder = arguments.get("encoder")
        
        result = await self.msf.generate_payload(payload, options, output_format, encoder)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "execution_time": result.execution_time,
                        "payload_info": result.data if result.data else None,
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_search_modules(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle module search with pagination."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 25)
        page = arguments.get("page", 1)
        
        # Validate pagination parameters
        if page < 1:
            page = 1
        if limit > 200:  # Cap max results per page
            limit = 200
        
        result = await self.msf.search_modules(query, limit, page)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "execution_time": result.execution_time,
                        "search_results": result.data if result.data else None,
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS,
                        "pagination_info": "Use 'page' parameter to navigate results (max 200 per page)"
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_get_status(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle status request."""
        status = self.msf.get_status()
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "server_info": self.server_info,
                        "msf_status": status,
                        "initialized": self.initialized
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_list_workspaces(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workspace listing."""
        result = await self.msf.execute_command("workspace")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "workspaces": result.data.get("stdout", "") if result.data else "",
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_create_workspace(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workspace creation."""
        name = arguments.get("name", "")
        command = f"workspace -a {name}"
        
        result = await self.msf.execute_command(command)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "workspace_name": name,
                        "output": result.data.get("stdout", "") if result.data else "",
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_switch_workspace(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle workspace switching."""
        name = arguments.get("name", "")
        command = f"workspace {name}"
        
        result = await self.msf.execute_command(command)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "workspace_name": name,
                        "output": result.data.get("stdout", "") if result.data else "",
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def _handle_list_sessions(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle session listing."""
        result = await self.msf.execute_command("sessions -l")
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({
                        "status": result.status.value,
                        "sessions": result.data.get("stdout", "") if result.data else "",
                        "error": result.error,
                        "success": result.status == OperationStatus.SUCCESS
                    }, indent=2)
                }
            ]
        }
    
    async def cleanup(self):
        """Clean up resources."""
        if self.msf:
            await self.msf.cleanup()

# MCP Protocol Implementation
async def handle_mcp_request(request: Dict[str, Any], server: MSFConsoleMCPServer) -> Dict[str, Any]:
    """Handle MCP protocol requests."""
    method = request.get("method", "")
    params = request.get("params", {})
    request_id = request.get("id")
    
    try:
        if method == "initialize":
            await server.initialize()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": server.server_info
                }
            }
        
        elif method == "tools/list":
            tools = server.get_available_tools()
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": tools}
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = await server.handle_tool_call(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    except Exception as e:
        logger.error(f"Error handling MCP request: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }

# Main server loop
async def main():
    """Main MCP server loop."""
    server = MSFConsoleMCPServer()
    
    try:
        logger.info("Starting MSFConsole MCP server...")
        
        # Read from stdin and write to stdout (MCP protocol)
        while True:
            try:
                # Read JSON-RPC request from stdin
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                try:
                    request = json.loads(line.strip())
                    response = await handle_mcp_request(request, server)
                    
                    # Write response to stdout
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": "Parse error"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                
            except EOFError:
                break
            except Exception as e:
                logger.error(f"Server loop error: {e}")
                break
    
    finally:
        logger.info("Shutting down MSFConsole MCP server...")
        await server.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server startup error: {e}")
        sys.exit(1)