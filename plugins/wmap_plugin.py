"""
WMAP Web Application Scanner Plugin for MSF Console MCP
Provides web application mapping and vulnerability scanning
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from msf_plugin_system import PluginInterface, PluginMetadata, PluginCategory, PluginContext, OperationResult

logger = logging.getLogger(__name__)


class WMAPPlugin(PluginInterface):
    """Web application mapping and scanning plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="wmap",
            description="Web application mapping and vulnerability scanner",
            category=PluginCategory.SCANNER,
            version="1.0.0",
            author="MSF MCP",
            dependencies=[],
            commands={
                "enable": "Enable WMAP scanner",
                "disable": "Disable WMAP scanner",
                "status": "Check WMAP status",
                "sites": "List discovered sites",
                "targets": "Manage scan targets",
                "modules": "List available WMAP modules",
                "run": "Run WMAP scan",
                "nodes": "Manage distributed scanning nodes",
                "reports": "Generate scan reports",
                "vulns": "List discovered vulnerabilities"
            },
            capabilities={"web_scanning", "vulnerability_detection", "site_mapping", "distributed_scanning"},
            auto_load=True,
            priority=85
        )
        
    def __init__(self, context: PluginContext):
        super().__init__(context)
        self._enabled = False
        self._sites = {}
        self._targets = []
        self._scan_results = {}
        self._available_modules = []
        
    async def initialize(self) -> OperationResult:
        """Initialize WMAP plugin"""
        try:
            # Load WMAP in MSF
            result = await self.msf.execute_command("load wmap")
            
            if "loaded" in result.output.lower():
                self._initialized = True
                
                # Get available WMAP modules
                await self._refresh_modules()
                
                return OperationResult(
                    success=True,
                    data={"status": "initialized", "modules": len(self._available_modules)},
                    metadata={"plugin": "wmap"}
                )
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Failed to load WMAP plugin in MSF",
                    metadata={"output": result.output}
                )
                
        except Exception as e:
            logger.error(f"Failed to initialize WMAP: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cleanup(self) -> OperationResult:
        """Cleanup WMAP plugin"""
        try:
            # Unload from MSF
            await self.msf.execute_command("unload wmap")
            
            return OperationResult(
                success=True,
                data={"status": "cleaned_up"},
                metadata={"plugin": "wmap"}
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup WMAP: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_enable(self, **kwargs) -> OperationResult:
        """Enable WMAP scanner"""
        self._enabled = True
        return OperationResult(
            success=True,
            data={"enabled": True},
            metadata={"action": "wmap_enable"}
        )
        
    async def cmd_sites(self, action: str = "list", url: Optional[str] = None, **kwargs) -> OperationResult:
        """Manage discovered sites"""
        try:
            if action == "list":
                result = await self.msf.execute_command("wmap_sites -l")
                sites = self._parse_sites(result.output)
                
                return OperationResult(
                    success=True,
                    data={"sites": sites},
                    metadata={"action": "wmap_sites_list", "count": len(sites)}
                )
                
            elif action == "add" and url:
                result = await self.msf.execute_command(f"wmap_sites -a {url}")
                
                return OperationResult(
                    success="Added" in result.output,
                    data={"url": url, "added": True},
                    output=result.output,
                    metadata={"action": "wmap_sites_add"}
                )
                
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Invalid sites action or missing URL"
                )
                
        except Exception as e:
            logger.error(f"WMAP sites error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_targets(self, action: str = "list", index: Optional[int] = None, **kwargs) -> OperationResult:
        """Manage scan targets"""
        try:
            if action == "list":
                result = await self.msf.execute_command("wmap_targets -l")
                targets = self._parse_targets(result.output)
                self._targets = targets
                
                return OperationResult(
                    success=True,
                    data={"targets": targets},
                    metadata={"action": "wmap_targets_list", "count": len(targets)}
                )
                
            elif action == "add" and index is not None:
                result = await self.msf.execute_command(f"wmap_targets -t {index}")
                
                return OperationResult(
                    success="Added" in result.output,
                    data={"index": index, "added": True},
                    output=result.output,
                    metadata={"action": "wmap_targets_add"}
                )
                
            elif action == "clear":
                result = await self.msf.execute_command("wmap_targets -c")
                self._targets.clear()
                
                return OperationResult(
                    success=True,
                    data={"cleared": True},
                    output=result.output,
                    metadata={"action": "wmap_targets_clear"}
                )
                
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Invalid targets action"
                )
                
        except Exception as e:
            logger.error(f"WMAP targets error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_run(self, test_mode: bool = False, modules: Optional[List[str]] = None, **kwargs) -> OperationResult:
        """Run WMAP scan"""
        try:
            if not self._enabled:
                return OperationResult(
                    success=False,
                    data=None,
                    error="WMAP scanner is not enabled"
                )
                
            if not self._targets:
                return OperationResult(
                    success=False,
                    data=None,
                    error="No targets configured"
                )
                
            # Run scan
            cmd = "wmap_run"
            if test_mode:
                cmd += " -t"
            if modules:
                cmd += f" -m {','.join(modules)}"
            else:
                cmd += " -e"  # Run all enabled modules
                
            result = await self.msf.execute_command(cmd, timeout=600)  # 10 minute timeout
            
            # Parse results
            vulns = self._parse_scan_results(result.output)
            self._scan_results[datetime.now().isoformat()] = vulns
            
            return OperationResult(
                success=True,
                data={
                    "scan_complete": True,
                    "vulnerabilities": len(vulns),
                    "targets_scanned": len(self._targets)
                },
                output=result.output,
                metadata={"action": "wmap_run", "test_mode": test_mode}
            )
            
        except Exception as e:
            logger.error(f"WMAP run error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_vulns(self, **kwargs) -> OperationResult:
        """List discovered vulnerabilities"""
        try:
            result = await self.msf.execute_command("wmap_vulns -l")
            vulns = self._parse_vulnerabilities(result.output)
            
            return OperationResult(
                success=True,
                data={"vulnerabilities": vulns},
                metadata={"action": "wmap_vulns", "count": len(vulns)}
            )
            
        except Exception as e:
            logger.error(f"WMAP vulns error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def _refresh_modules(self) -> None:
        """Refresh available WMAP modules"""
        try:
            result = await self.msf.execute_command("wmap_modules -l")
            self._available_modules = self._parse_modules(result.output)
        except Exception as e:
            logger.error(f"Failed to refresh WMAP modules: {e}")
            
    def _parse_sites(self, output: str) -> List[Dict[str, Any]]:
        """Parse sites from WMAP output"""
        sites = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if 'http' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    sites.append({
                        "id": parts[0],
                        "url": parts[1],
                        "vhost": parts[2] if len(parts) > 2 else ""
                    })
                    
        return sites
        
    def _parse_targets(self, output: str) -> List[Dict[str, Any]]:
        """Parse targets from WMAP output"""
        targets = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('['):
                parts = line.split()
                if len(parts) >= 2:
                    targets.append({
                        "index": len(targets),
                        "url": parts[0],
                        "status": parts[1] if len(parts) > 1 else "pending"
                    })
                    
        return targets
        
    def _parse_scan_results(self, output: str) -> List[Dict[str, Any]]:
        """Parse scan results from WMAP output"""
        vulns = []
        current_vuln = None
        
        for line in output.split('\n'):
            if '[+]' in line and 'found' in line.lower():
                if current_vuln:
                    vulns.append(current_vuln)
                current_vuln = {
                    "finding": line.strip(),
                    "details": []
                }
            elif current_vuln and line.strip():
                current_vuln["details"].append(line.strip())
                
        if current_vuln:
            vulns.append(current_vuln)
            
        return vulns
        
    def _parse_vulnerabilities(self, output: str) -> List[Dict[str, Any]]:
        """Parse vulnerabilities from WMAP output"""
        vulns = []
        lines = output.strip().split('\n')
        
        for line in lines:
            if line.strip() and not line.startswith('['):
                parts = line.split(None, 3)
                if len(parts) >= 4:
                    vulns.append({
                        "timestamp": parts[0],
                        "host": parts[1],
                        "port": parts[2],
                        "vulnerability": parts[3]
                    })
                    
        return vulns
        
    def _parse_modules(self, output: str) -> List[str]:
        """Parse available modules from WMAP output"""
        modules = []
        
        for line in output.split('\n'):
            if 'auxiliary/' in line:
                module = line.strip().split()[0]
                modules.append(module)
                
        return modules