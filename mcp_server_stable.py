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
from msf_extended_tools import MSFExtendedTools, ExtendedOperationResult
from msf_final_five_tools import MSFFinalFiveTools, FinalOperationResult

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
        self.extended_msf = MSFExtendedTools()
        self.final_msf = MSFFinalFiveTools()
        self.initialized = False
        self.server_info = {
            "name": "msfconsole-stable",
            "version": "3.0.0",
            "description": "Production-ready MSFConsole MCP server with 100% coverage (28 tools)",
            "tools_count": 28,
            "coverage": "100%"
        }
    
    async def initialize(self):
        """Initialize both standard and extended MSFConsole integrations."""
        if not self.initialized:
            logger.info("Initializing MSFConsole MCP server with extended tools...")
            
            # Initialize standard wrapper
            result = await self.msf.initialize()
            if result.status != OperationStatus.SUCCESS:
                logger.error(f"Standard MSFConsole initialization failed: {result.error}")
                return False
            
            # Initialize extended wrapper
            extended_result = await self.extended_msf.initialize()
            if extended_result.status != OperationStatus.SUCCESS:
                logger.error(f"Extended MSFConsole initialization failed: {extended_result.error}")
                return False
            
            # Initialize final five wrapper
            final_result = await self.final_msf.initialize()
            if final_result.status != OperationStatus.SUCCESS:
                logger.error(f"Final five tools initialization failed: {final_result.error}")
                return False
            
            self.initialized = True
            logger.info("MSFConsole MCP server with 100% coverage initialized successfully (28 tools)")
            return True
            
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
                "description": "Search for MSF modules with pagination support and automatic token management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'exploit platform:windows'). Use specific terms to reduce results."
                        },
                        "limit": {
                            "type": "number",
                            "description": "Maximum number of results per page (automatically reduced if needed to fit token limits)",
                            "default": 10,
                            "minimum": 1,
                            "maximum": 50
                        },
                        "page": {
                            "type": "number",
                            "description": "Page number (1-based)",
                            "default": 1,
                            "minimum": 1
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
            },
            # Extended Tools (15 new tools)
            {
                "name": "msf_module_manager",
                "description": "Complete module lifecycle management including loading, configuration, and execution",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["load", "configure", "validate", "execute", "reload", "info"], "description": "Module management action"},
                        "module_path": {"type": "string", "description": "Full module path"},
                        "options": {"type": "object", "description": "Module options", "additionalProperties": {"type": "string"}},
                        "advanced_options": {"type": "object", "description": "Advanced/evasion options", "additionalProperties": {"type": "string"}},
                        "timeout": {"type": "number", "description": "Optional adaptive timeout"}
                    },
                    "required": ["action", "module_path"]
                }
            },
            {
                "name": "msf_session_interact",
                "description": "Advanced session interaction with command execution and file operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "session_id": {"type": "string", "description": "Target session ID"},
                        "action": {"type": "string", "enum": ["shell", "execute", "upload", "download", "screenshot", "migrate"], "description": "Session interaction action"},
                        "command": {"type": "string", "description": "Command to execute (for execute action)"},
                        "source_path": {"type": "string", "description": "Source file path (for upload/download)"},
                        "target_path": {"type": "string", "description": "Target file path (for upload/download)"},
                        "process_id": {"type": "integer", "description": "Process ID (for migrate action)"},
                        "timeout": {"type": "number", "description": "Optional timeout"}
                    },
                    "required": ["session_id", "action"]
                }
            },
            {
                "name": "msf_database_query",
                "description": "Advanced database operations for data persistence and analysis",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string", "enum": ["query", "export", "import", "analyze", "backup", "restore"], "description": "Database operation type"},
                        "query": {"type": "string", "description": "SQL query (for query operation)"},
                        "format": {"type": "string", "enum": ["json", "csv", "xml", "yaml"], "default": "json", "description": "Output format"},
                        "file_path": {"type": "string", "description": "File path (for import/export/backup/restore)"},
                        "filters": {"type": "object", "description": "Query filters", "additionalProperties": True},
                        "pagination": {"type": "object", "description": "Pagination settings", "properties": {"page": {"type": "integer"}, "limit": {"type": "integer"}}}
                    },
                    "required": ["operation"]
                }
            },
            {
                "name": "msf_exploit_chain",
                "description": "Automate complex multi-stage exploitation workflows",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create", "add_step", "configure", "validate", "execute", "monitor"], "description": "Chain operation"},
                        "chain_name": {"type": "string", "description": "Exploitation chain name"},
                        "step_config": {"type": "object", "description": "Step configuration", "additionalProperties": True},
                        "execution_mode": {"type": "string", "enum": ["sequential", "parallel", "conditional"], "default": "sequential"},
                        "rollback_on_failure": {"type": "boolean", "default": True}
                    },
                    "required": ["action", "chain_name"]
                }
            },
            {
                "name": "msf_post_exploitation",
                "description": "Comprehensive post-exploitation module management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string", "enum": ["enumerate", "gather", "persist", "escalate", "lateral", "cleanup"], "description": "Post-exploitation category"},
                        "module_name": {"type": "string", "description": "Module name"},
                        "session_id": {"type": "string", "description": "Target session ID"},
                        "options": {"type": "object", "description": "Module options", "additionalProperties": {"type": "string"}},
                        "stealth_mode": {"type": "boolean", "default": False}
                    },
                    "required": ["category", "module_name", "session_id"]
                }
            },
            {
                "name": "msf_handler_manager",
                "description": "Payload handler lifecycle management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create", "start", "stop", "list", "monitor", "auto_migrate"], "description": "Handler action"},
                        "handler_name": {"type": "string", "description": "Handler identifier"},
                        "payload_type": {"type": "string", "description": "Payload type (e.g., windows/meterpreter/reverse_tcp)"},
                        "options": {"type": "object", "description": "Handler options", "additionalProperties": {"type": "string"}},
                        "auto_options": {"type": "object", "description": "Auto-migration options", "additionalProperties": True}
                    },
                    "required": ["action", "handler_name"]
                }
            },
            {
                "name": "msf_scanner_suite",
                "description": "Comprehensive scanning and discovery operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "scanner_type": {"type": "string", "enum": ["network", "service", "vulnerability", "credential", "web", "custom"], "description": "Scanner category"},
                        "targets": {"type": ["string", "array"], "description": "Target hosts or networks"},
                        "options": {"type": "object", "description": "Scanner options", "additionalProperties": {"type": "string"}},
                        "threads": {"type": "integer", "default": 10, "description": "Number of threads"},
                        "output_format": {"type": "string", "enum": ["table", "json", "csv"], "default": "table"}
                    },
                    "required": ["scanner_type", "targets"]
                }
            },
            {
                "name": "msf_credential_manager",
                "description": "Centralized credential management and usage",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add", "list", "test", "spray", "export", "import"], "description": "Credential action"},
                        "credential_data": {"type": "object", "description": "Credential information", "additionalProperties": True},
                        "filters": {"type": "object", "description": "Filter criteria", "additionalProperties": {"type": "string"}},
                        "targets": {"type": "array", "items": {"type": "string"}, "description": "Target hosts"},
                        "format": {"type": "string", "enum": ["json", "csv", "xml"], "default": "json"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_pivot_manager",
                "description": "Network pivoting and routing management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add_route", "remove_route", "list_routes", "setup_proxy", "port_forward", "auto_route"], "description": "Pivot operation"},
                        "session_id": {"type": "string", "description": "Session for pivoting"},
                        "network": {"type": "string", "description": "Target network (CIDR)"},
                        "options": {"type": "object", "description": "Pivot options", "additionalProperties": True}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_resource_executor",
                "description": "Resource script execution and management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["execute", "validate", "create", "list", "schedule", "monitor"], "description": "Resource action"},
                        "script_path": {"type": "string", "description": "Path to resource script"},
                        "script_content": {"type": "string", "description": "Script content (for create action)"},
                        "variables": {"type": "object", "description": "Script variables", "additionalProperties": {"type": "string"}},
                        "schedule_config": {"type": "object", "description": "Scheduling configuration", "additionalProperties": True}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_loot_collector",
                "description": "Automated loot collection and organization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["collect", "organize", "search", "export", "analyze", "tag"], "description": "Loot action"},
                        "session_id": {"type": "string", "description": "Source session"},
                        "loot_type": {"type": "string", "description": "Type of loot to collect"},
                        "filters": {"type": "object", "description": "Search/filter criteria", "additionalProperties": True},
                        "tags": {"type": "array", "items": {"type": "string"}, "description": "Loot tags"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_vulnerability_tracker",
                "description": "Vulnerability tracking and management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["add", "update", "search", "report", "correlate", "prioritize"], "description": "Vulnerability action"},
                        "vulnerability_data": {"type": "object", "description": "Vulnerability information", "additionalProperties": True},
                        "filters": {"type": "object", "description": "Search filters", "additionalProperties": {"type": "string"}},
                        "report_format": {"type": "string", "enum": ["json", "pdf", "html", "csv"], "default": "json"},
                        "correlation_depth": {"type": "integer", "default": 1}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_reporting_engine",
                "description": "Comprehensive reporting and documentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "report_type": {"type": "string", "enum": ["executive", "technical", "compliance", "pentest", "incident", "custom"], "description": "Report type"},
                        "workspace": {"type": "string", "description": "Source workspace"},
                        "filters": {"type": "object", "description": "Data filters", "additionalProperties": True},
                        "template": {"type": "string", "description": "Report template"},
                        "output_format": {"type": "string", "enum": ["pdf", "html", "docx", "markdown"], "default": "pdf"},
                        "include_evidence": {"type": "boolean", "default": True}
                    },
                    "required": ["report_type", "workspace"]
                }
            },
            {
                "name": "msf_automation_builder",
                "description": "Visual workflow automation and playbook creation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["create_workflow", "add_node", "connect_nodes", "validate", "execute", "export"], "description": "Automation action"},
                        "workflow_name": {"type": "string", "description": "Workflow identifier"},
                        "node_config": {"type": "object", "description": "Node configuration", "additionalProperties": True},
                        "connections": {"type": "array", "items": {"type": "object"}, "description": "Node connections"},
                        "execution_params": {"type": "object", "description": "Execution parameters", "additionalProperties": True}
                    },
                    "required": ["action", "workflow_name"]
                }
            },
            {
                "name": "msf_plugin_manager",
                "description": "Plugin and extension management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["list", "load", "unload", "configure", "status", "update"], "description": "Plugin action"},
                        "plugin_name": {"type": "string", "description": "Plugin name"},
                        "config": {"type": "object", "description": "Plugin configuration", "additionalProperties": True},
                        "auto_load": {"type": "boolean", "default": False}
                    },
                    "required": ["action"]
                }
            },
            # Final Five Tools for 100% Coverage
            {
                "name": "msf_core_system_manager",
                "description": "Complete core system functionality including banner, connect, debug, spool, threads, and plugin management",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["banner", "color", "tips", "features", "connect", "debug", "spool", "time", "threads", "history", "grep", "load", "unload", "reload_lib"], "description": "System action"},
                        "target": {"type": "string", "description": "Target for specific actions (host for connect, plugin for load/unload, etc.)"},
                        "options": {"type": "object", "description": "Additional options for the action", "additionalProperties": True}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_advanced_module_controller",
                "description": "Complete module stack and advanced operations including back, clearm, listm, popm, pushm, favorites",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["back", "clearm", "listm", "popm", "pushm", "previous", "favorites", "favorite", "loadpath", "reload_all", "advanced", "show"], "description": "Module action"},
                        "module_path": {"type": "string", "description": "Module path for specific operations"},
                        "stack_operation": {"type": "string", "description": "Stack operation type"},
                        "show_type": {"type": "string", "description": "Type of modules to show (exploits, payloads, auxiliary, etc.)"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_job_manager",
                "description": "Complete job lifecycle management including handler start, job listing, killing, and renaming",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["jobs", "handler", "kill", "rename_job", "monitor", "background"], "description": "Job action"},
                        "job_id": {"type": "string", "description": "Job ID for specific operations"},
                        "handler_config": {"type": "object", "description": "Handler configuration", "additionalProperties": {"type": "string"}},
                        "job_name": {"type": "string", "description": "New name for rename operation"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_database_admin_controller",
                "description": "Complete database administration including connect, export, import, analyze, and nmap integration",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["db_connect", "db_disconnect", "db_save", "db_export", "db_import", "db_nmap", "db_stats", "db_remove", "db_rebuild_cache", "analyze"], "description": "Database action"},
                        "connection_string": {"type": "string", "description": "Database connection string"},
                        "file_path": {"type": "string", "description": "File path for import/export"},
                        "export_format": {"type": "string", "enum": ["xml", "csv", "pwdump"], "default": "xml", "description": "Export format"},
                        "nmap_options": {"type": "string", "description": "Nmap scan options"}
                    },
                    "required": ["action"]
                }
            },
            {
                "name": "msf_developer_debug_suite",
                "description": "Development and debugging capabilities including edit, pry, irb, log, time, dns, and makerc",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "string", "enum": ["edit", "pry", "irb", "log", "time", "dns", "makerc"], "description": "Developer action"},
                        "target": {"type": "string", "description": "Target module/file to edit"},
                        "command_to_time": {"type": "string", "description": "Command to measure execution time"},
                        "dns_config": {"type": "object", "description": "DNS configuration options", "additionalProperties": True},
                        "output_file": {"type": "string", "description": "Output file for makerc"}
                    },
                    "required": ["action"]
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
            # Extended tools (15 new tools)
            elif tool_name in ["msf_module_manager", "msf_session_interact", "msf_database_query",
                             "msf_exploit_chain", "msf_post_exploitation", "msf_handler_manager",
                             "msf_scanner_suite", "msf_credential_manager", "msf_pivot_manager",
                             "msf_resource_executor", "msf_loot_collector", "msf_vulnerability_tracker",
                             "msf_reporting_engine", "msf_automation_builder", "msf_plugin_manager"]:
                return await self._handle_extended_tool(tool_name, arguments)
            # Final five tools (100% coverage)
            elif tool_name in ["msf_core_system_manager", "msf_advanced_module_controller",
                             "msf_job_manager", "msf_database_admin_controller",
                             "msf_developer_debug_suite"]:
                return await self._handle_final_tool(tool_name, arguments)
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: Unknown tool '{tool_name}' (Available: 28 tools total)"
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
    
    async def _handle_extended_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle extended 15 tools using extended wrapper."""
        try:
            # Map tool names to methods
            method_name = tool_name  # Direct mapping since names match
            method = getattr(self.extended_msf, method_name)
            
            # Call the method with arguments
            result = await method(**arguments)
            
            return self._format_extended_result(result)
        
        except AttributeError:
            return {"content": [{"type": "text", "text": f"Extended tool method not found: {tool_name}"}]}
        except Exception as e:
            logger.error(f"Extended tool error {tool_name}: {e}")
            return {"content": [{"type": "text", "text": f"Extended tool error: {str(e)}"}]}
    
    def _format_extended_result(self, result: ExtendedOperationResult) -> Dict[str, Any]:
        """Format extended operation result for MCP response."""
        response_data = {
            "status": result.status.value,
            "execution_time": result.execution_time,
            "success": result.status == OperationStatus.SUCCESS,
            "data": result.data,
            "error": result.error
        }
        
        # Add extended fields if available
        if hasattr(result, 'metadata') and result.metadata:
            response_data["metadata"] = result.metadata
        
        if hasattr(result, 'warnings') and result.warnings:
            response_data["warnings"] = result.warnings
        
        if hasattr(result, 'suggestions') and result.suggestions:
            response_data["suggestions"] = result.suggestions
        
        return {"content": [{"type": "text", "text": json.dumps(response_data, indent=2)}]}
    
    async def _handle_final_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle final five tools using final wrapper."""
        try:
            # Map tool names to methods
            method_name = tool_name  # Direct mapping since names match
            method = getattr(self.final_msf, method_name)
            
            # Call the method with arguments
            result = await method(**arguments)
            
            return self._format_final_result(result)
        
        except AttributeError:
            return {"content": [{"type": "text", "text": f"Final tool method not found: {tool_name}"}]}
        except Exception as e:
            logger.error(f"Final tool error {tool_name}: {e}")
            return {"content": [{"type": "text", "text": f"Final tool error: {str(e)}"}]}
    
    def _format_final_result(self, result: FinalOperationResult) -> Dict[str, Any]:
        """Format final operation result for MCP response."""
        response_data = {
            "status": result.status.value,
            "execution_time": result.execution_time,
            "success": result.status == OperationStatus.SUCCESS,
            "data": result.data,
            "error": result.error
        }
        
        # Add final tool specific fields
        if hasattr(result, 'command_executed') and result.command_executed:
            response_data["command_executed"] = result.command_executed
        
        if hasattr(result, 'affected_items') and result.affected_items:
            response_data["affected_items"] = result.affected_items
        
        if hasattr(result, 'system_state') and result.system_state:
            response_data["system_state"] = result.system_state
        
        return {"content": [{"type": "text", "text": json.dumps(response_data, indent=2)}]}
    
    async def cleanup(self):
        """Clean up resources."""
        if self.msf:
            await self.msf.cleanup()
        if self.extended_msf:
            await self.extended_msf.cleanup()
        if self.final_msf:
            await self.final_msf.cleanup()

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