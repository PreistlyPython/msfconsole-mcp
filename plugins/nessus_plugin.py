"""
Nessus Integration Plugin for MSF Console MCP
Provides comprehensive Nessus vulnerability scanner integration
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from msf_plugin_system import PluginInterface, PluginMetadata, PluginCategory, PluginContext, OperationResult

logger = logging.getLogger(__name__)


class NessusPlugin(PluginInterface):
    """Nessus vulnerability scanner integration plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="nessus",
            description="Nessus vulnerability scanner integration for MSF",
            category=PluginCategory.SCANNER,
            version="1.0.0",
            author="MSF MCP",
            dependencies=[],
            commands={
                "connect": "Connect to Nessus server",
                "disconnect": "Disconnect from Nessus server",
                "status": "Check Nessus connection status",
                "list_scans": "List all Nessus scans",
                "scan_info": "Get information about a specific scan",
                "launch_scan": "Launch a Nessus scan",
                "pause_scan": "Pause a running scan",
                "resume_scan": "Resume a paused scan",
                "stop_scan": "Stop a running scan",
                "list_policies": "List available scan policies",
                "import_results": "Import Nessus results into MSF database",
                "list_reports": "List available Nessus reports",
                "export_report": "Export a Nessus report"
            },
            capabilities={"scanner", "vulnerability_detection", "report_generation", "database_import"},
            auto_load=True,
            priority=90
        )
        
    def __init__(self, context: PluginContext):
        super().__init__(context)
        self._connected = False
        self._server_url = None
        self._token = None
        self._scans = {}
        self._policies = {}
        
    async def initialize(self) -> OperationResult:
        """Initialize Nessus plugin"""
        try:
            # Check if Nessus integration is available in MSF
            result = await self.msf.execute_command("load nessus")
            
            if "Plugin loaded" in result.output or "already loaded" in result.output:
                self._initialized = True
                return OperationResult(
                    success=True,
                    data={"status": "initialized"},
                    metadata={"plugin": "nessus"}
                )
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Failed to load Nessus plugin in MSF",
                    metadata={"output": result.output}
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize Nessus plugin: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cleanup(self) -> OperationResult:
        """Cleanup Nessus plugin resources"""
        try:
            if self._connected:
                await self.cmd_disconnect()
                
            # Unload from MSF
            await self.msf.execute_command("unload nessus")
            
            return OperationResult(
                success=True,
                data={"status": "cleaned_up"},
                metadata={"plugin": "nessus"}
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup Nessus plugin: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_connect(self, server: str, username: str, password: str, **kwargs) -> OperationResult:
        """Connect to Nessus server"""
        try:
            # Execute Nessus connect command
            cmd = f"nessus_connect {server} {username} {password}"
            result = await self.msf.execute_command(cmd)
            
            if "Successfully authenticated" in result.output or "Connected" in result.output:
                self._connected = True
                self._server_url = server
                
                return OperationResult(
                    success=True,
                    data={
                        "status": "connected",
                        "server": server,
                        "user": username
                    },
                    metadata={"action": "nessus_connect"}
                )
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Failed to connect to Nessus",
                    metadata={"output": result.output}
                )
                
        except Exception as e:
            logger.error(f"Failed to connect to Nessus: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_disconnect(self, **kwargs) -> OperationResult:
        """Disconnect from Nessus server"""
        try:
            result = await self.msf.execute_command("nessus_logout")
            
            self._connected = False
            self._server_url = None
            self._token = None
            
            return OperationResult(
                success=True,
                data={"status": "disconnected"},
                metadata={"action": "nessus_disconnect"}
            )
            
        except Exception as e:
            logger.error(f"Failed to disconnect from Nessus: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_status(self, **kwargs) -> OperationResult:
        """Check Nessus connection status"""
        try:
            if not self._connected:
                return OperationResult(
                    success=True,
                    data={
                        "connected": False,
                        "server": None
                    },
                    metadata={"action": "nessus_status"}
                )
                
            # Verify connection with a simple command
            result = await self.msf.execute_command("nessus_server_status")
            
            return OperationResult(
                success=True,
                data={
                    "connected": True,
                    "server": self._server_url,
                    "status": result.output
                },
                metadata={"action": "nessus_status"}
            )
            
        except Exception as e:
            logger.error(f"Failed to check Nessus status: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_list_scans(self, **kwargs) -> OperationResult:
        """List all Nessus scans"""
        try:
            if not self._connected:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Not connected to Nessus server"
                )
                
            result = await self.msf.execute_command("nessus_scan_list")
            
            # Parse scan list from output
            scans = self._parse_scan_list(result.output)
            self._scans = {scan["id"]: scan for scan in scans}
            
            return OperationResult(
                success=True,
                data={"scans": scans},
                metadata={"action": "nessus_list_scans", "count": len(scans)}
            )
            
        except Exception as e:
            logger.error(f"Failed to list Nessus scans: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_launch_scan(self, policy_id: str, targets: str, name: Optional[str] = None, **kwargs) -> OperationResult:
        """Launch a new Nessus scan"""
        try:
            if not self._connected:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Not connected to Nessus server"
                )
                
            # Generate scan name if not provided
            if not name:
                from datetime import datetime
                name = f"MSF_Scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
            cmd = f"nessus_scan_create {policy_id} {name} {targets}"
            result = await self.msf.execute_command(cmd)
            
            if "created" in result.output.lower():
                # Launch the created scan
                scan_id = self._extract_scan_id(result.output)
                if scan_id:
                    launch_result = await self.msf.execute_command(f"nessus_scan_launch {scan_id}")
                    
                    return OperationResult(
                        success=True,
                        data={
                            "scan_id": scan_id,
                            "name": name,
                            "targets": targets,
                            "status": "launched"
                        },
                        metadata={"action": "nessus_launch_scan"}
                    )
                    
            return OperationResult(
                success=False,
                data=None,
                error="Failed to launch scan",
                metadata={"output": result.output}
            )
            
        except Exception as e:
            logger.error(f"Failed to launch Nessus scan: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_import_results(self, scan_id: str, **kwargs) -> OperationResult:
        """Import Nessus scan results into MSF database"""
        try:
            if not self._connected:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Not connected to Nessus server"
                )
                
            # Export scan results
            export_cmd = f"nessus_report_download {scan_id} nessus"
            export_result = await self.msf.execute_command(export_cmd)
            
            if "downloaded" in export_result.output.lower():
                # Import into MSF database
                import_cmd = f"db_import_nessus {scan_id}"
                import_result = await self.msf.execute_command(import_cmd)
                
                # Parse import statistics
                stats = self._parse_import_stats(import_result.output)
                
                return OperationResult(
                    success=True,
                    data={
                        "scan_id": scan_id,
                        "imported": True,
                        "statistics": stats
                    },
                    metadata={"action": "nessus_import_results"}
                )
                
            return OperationResult(
                success=False,
                data=None,
                error="Failed to import scan results",
                metadata={"output": export_result.output}
            )
            
        except Exception as e:
            logger.error(f"Failed to import Nessus results: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    def _parse_scan_list(self, output: str) -> List[Dict[str, Any]]:
        """Parse scan list from Nessus output"""
        scans = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'Scan ID' in line or '---' in line or not line.strip():
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                scans.append({
                    "id": parts[0],
                    "name": ' '.join(parts[1:-1]),
                    "status": parts[-1]
                })
                
        return scans
        
    def _extract_scan_id(self, output: str) -> Optional[str]:
        """Extract scan ID from command output"""
        import re
        match = re.search(r'Scan ID[:\s]+(\d+)', output)
        if match:
            return match.group(1)
        return None
        
    def _parse_import_stats(self, output: str) -> Dict[str, int]:
        """Parse import statistics from output"""
        stats = {
            "hosts": 0,
            "services": 0,
            "vulnerabilities": 0
        }
        
        import re
        hosts_match = re.search(r'(\d+)\s+hosts?', output)
        if hosts_match:
            stats["hosts"] = int(hosts_match.group(1))
            
        services_match = re.search(r'(\d+)\s+services?', output)
        if services_match:
            stats["services"] = int(services_match.group(1))
            
        vulns_match = re.search(r'(\d+)\s+vulnerabilit', output)
        if vulns_match:
            stats["vulnerabilities"] = int(vulns_match.group(1))
            
        return stats