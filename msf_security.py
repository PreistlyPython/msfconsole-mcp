#!/usr/bin/env python3

"""
Enhanced Security Features for MSF MCP
--------------------------------------
Comprehensive security validation, audit logging, and threat detection.
"""

import logging
import json
import time
import hashlib
import re
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)

class ThreatLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ActionType(Enum):
    COMMAND_EXECUTION = "command_execution"
    MODULE_USAGE = "module_usage"
    PAYLOAD_GENERATION = "payload_generation"
    SESSION_INTERACTION = "session_interaction"
    DATABASE_ACCESS = "database_access"
    WORKSPACE_CHANGE = "workspace_change"

@dataclass
class SecurityEvent:
    timestamp: float
    action_type: ActionType
    threat_level: ThreatLevel
    user_context: str
    command: str
    details: Dict[str, Any] = field(default_factory=dict)
    blocked: bool = False
    risk_score: int = 0

@dataclass
class SecurityPolicy:
    max_command_length: int = 1000
    allowed_file_extensions: Set[str] = field(default_factory=lambda: {'.rc', '.txt', '.log'})
    blocked_keywords: Set[str] = field(default_factory=lambda: {
        'rm -rf', 'format', 'fdisk', 'dd if=', 'shutdown', 'reboot',
        'del /f', 'rmdir /s', 'net user', 'net localgroup'
    })
    max_payload_size: int = 10 * 1024 * 1024  # 10MB
    session_timeout: int = 3600  # 1 hour
    max_concurrent_sessions: int = 10
    enable_audit_logging: bool = True
    require_workspace_isolation: bool = True

class MSFSecurityManager:
    """
    Comprehensive security manager for MSF MCP operations.
    Handles validation, threat detection, audit logging, and access control.
    """
    
    def __init__(self, policy: SecurityPolicy = None):
        self.policy = policy or SecurityPolicy()
        self.security_events: List[SecurityEvent] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.command_history: List[Dict[str, Any]] = []
        self.threat_patterns = self._load_threat_patterns()
        self.audit_log_path = Path("msf_security_audit.log")
        
        # Set up audit logging
        if self.policy.enable_audit_logging:
            self._setup_audit_logging()
    
    def _setup_audit_logging(self):
        """Set up dedicated audit logging."""
        audit_handler = logging.FileHandler(self.audit_log_path)
        audit_formatter = logging.Formatter(
            '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
        )
        audit_handler.setFormatter(audit_formatter)
        
        self.audit_logger = logging.getLogger('msf_security_audit')
        self.audit_logger.setLevel(logging.INFO)
        self.audit_logger.addHandler(audit_handler)
        self.audit_logger.propagate = False
    
    def _load_threat_patterns(self) -> Dict[str, List[str]]:
        """Load threat detection patterns."""
        return {
            'system_commands': [
                r'\b(rm|del|format|fdisk|dd)\s+',
                r'\b(shutdown|reboot|halt|poweroff)\b',
                r'\b(passwd|useradd|usermod|userdel)\b',
                r'\b(chmod|chown|chgrp)\s+777',
                r'\b(wget|curl|nc|netcat)\s+.*\|\s*(sh|bash|cmd)'
            ],
            'network_exposure': [
                r'bind_tcp.*LHOST=0\.0\.0\.0',
                r'bind_tcp.*LHOST=\*',
                r'reverse_tcp.*LHOST=0\.0\.0\.0'
            ],
            'privilege_escalation': [
                r'exploit/.*/(local|privilege)',
                r'post/.*/(gather|escalate)',
                r'auxiliary/.*/(gather|scanner).*password'
            ],
            'persistence': [
                r'post/.*/persistence',
                r'exploit/.*/persistence',
                r'auxiliary/.*/persistence'
            ],
            'data_exfiltration': [
                r'post/.*/gather',
                r'auxiliary/.*/gather',
                r'download\s+.*\.(txt|doc|pdf|xls|db|sql)'
            ]
        }
    
    async def validate_command(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive command validation with threat detection.
        
        Args:
            command: Command to validate
            context: Execution context
            
        Returns:
            Dict containing validation results and security assessment
        """
        context = context or {}
        start_time = time.time()
        
        # Basic sanitization
        sanitized_command = self._sanitize_command(command)
        
        # Validation checks
        validation_results = {
            'valid': True,
            'sanitized_command': sanitized_command,
            'threat_level': ThreatLevel.LOW,
            'risk_score': 0,
            'warnings': [],
            'blocked_reasons': [],
            'recommendations': []
        }
        
        # Length check
        if len(command) > self.policy.max_command_length:
            validation_results['valid'] = False
            validation_results['blocked_reasons'].append(
                f"Command exceeds maximum length ({self.policy.max_command_length})"
            )
            validation_results['risk_score'] += 20
        
        # Keyword blocking
        for keyword in self.policy.blocked_keywords:
            if keyword.lower() in command.lower():
                validation_results['valid'] = False
                validation_results['blocked_reasons'].append(f"Contains blocked keyword: {keyword}")
                validation_results['threat_level'] = ThreatLevel.HIGH
                validation_results['risk_score'] += 50
        
        # Threat pattern detection
        threat_analysis = await self._analyze_threats(command)
        validation_results.update(threat_analysis)
        
        # Context-specific validation
        if context.get('workspace') == 'production':
            validation_results['warnings'].append("Executing in production workspace")
            validation_results['risk_score'] += 10
        
        # Module-specific validation
        if command.strip().startswith('use '):
            module_validation = self._validate_module_usage(command)
            validation_results.update(module_validation)
        
        # Log security event
        await self._log_security_event(
            ActionType.COMMAND_EXECUTION,
            validation_results['threat_level'],
            command,
            context,
            blocked=not validation_results['valid'],
            risk_score=validation_results['risk_score']
        )
        
        validation_results['validation_time'] = time.time() - start_time
        return validation_results
    
    async def validate_payload_generation(self, payload_type: str, options: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate payload generation requests for security risks.
        
        Args:
            payload_type: Type of payload being generated
            options: Payload options
            
        Returns:
            Dict containing validation results
        """
        validation_results = {
            'valid': True,
            'threat_level': ThreatLevel.MEDIUM,  # Payloads are inherently risky
            'risk_score': 25,  # Base risk for payload generation
            'warnings': [],
            'blocked_reasons': [],
            'recommendations': []
        }
        
        # Check for dangerous payload types
        dangerous_payloads = [
            'windows/exec', 'linux/x86/exec', 'cmd/unix/bind_netcat'
        ]
        
        for dangerous in dangerous_payloads:
            if dangerous in payload_type:
                validation_results['threat_level'] = ThreatLevel.HIGH
                validation_results['risk_score'] += 30
                validation_results['warnings'].append(
                    f"Dangerous payload type detected: {payload_type}"
                )
        
        # Check LHOST configuration
        lhost = options.get('LHOST', '')
        if lhost in ['0.0.0.0', '*', '']:
            validation_results['threat_level'] = ThreatLevel.HIGH
            validation_results['risk_score'] += 25
            validation_results['warnings'].append(
                "Payload configured to bind to all interfaces (security risk)"
            )
            validation_results['recommendations'].append(
                "Specify a specific LHOST IP address"
            )
        
        # Check for common exploit payloads
        if 'meterpreter' in payload_type:
            validation_results['warnings'].append(
                "Meterpreter payload detected - ensure authorized use"
            )
            validation_results['risk_score'] += 15
        
        # Log payload generation event
        await self._log_security_event(
            ActionType.PAYLOAD_GENERATION,
            validation_results['threat_level'],
            f"Payload: {payload_type}",
            {'options': options},
            risk_score=validation_results['risk_score']
        )
        
        return validation_results
    
    async def validate_session_interaction(self, session_id: str, action: str) -> Dict[str, Any]:
        """
        Validate session interaction attempts.
        
        Args:
            session_id: Session ID
            action: Action being performed
            
        Returns:
            Dict containing validation results
        """
        validation_results = {
            'valid': True,
            'threat_level': ThreatLevel.MEDIUM,
            'risk_score': 20,
            'warnings': [],
            'blocked_reasons': []
        }
        
        # Check session limits
        if len(self.active_sessions) >= self.policy.max_concurrent_sessions:
            validation_results['valid'] = False
            validation_results['blocked_reasons'].append(
                f"Maximum concurrent sessions exceeded ({self.policy.max_concurrent_sessions})"
            )
            validation_results['threat_level'] = ThreatLevel.HIGH
            validation_results['risk_score'] += 30
        
        # Track session activity
        if session_id not in self.active_sessions:
            self.active_sessions[session_id] = {
                'created_at': time.time(),
                'last_activity': time.time(),
                'action_count': 0
            }
        else:
            session_info = self.active_sessions[session_id]
            session_info['last_activity'] = time.time()
            session_info['action_count'] += 1
            
            # Check for session timeout
            if (time.time() - session_info['created_at']) > self.policy.session_timeout:
                validation_results['warnings'].append(
                    f"Session {session_id} has exceeded timeout limit"
                )
                validation_results['risk_score'] += 15
        
        # Validate specific actions
        if action in ['execute', 'shell']:
            validation_results['threat_level'] = ThreatLevel.HIGH
            validation_results['risk_score'] += 25
            validation_results['warnings'].append(
                f"High-risk session action: {action}"
            )
        
        # Log session interaction
        await self._log_security_event(
            ActionType.SESSION_INTERACTION,
            validation_results['threat_level'],
            f"Session {session_id}: {action}",
            {'session_id': session_id, 'action': action},
            risk_score=validation_results['risk_score']
        )
        
        return validation_results
    
    def _sanitize_command(self, command: str) -> str:
        """Sanitize command input."""
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', command)
        
        # Remove dangerous character sequences
        sanitized = re.sub(r'[;&|`$()]', '', sanitized)
        
        # Limit length
        if len(sanitized) > self.policy.max_command_length:
            sanitized = sanitized[:self.policy.max_command_length]
        
        return sanitized.strip()
    
    async def _analyze_threats(self, command: str) -> Dict[str, Any]:
        """Analyze command for threat patterns."""
        threat_results = {
            'threat_level': ThreatLevel.LOW,
            'risk_score': 0,
            'threats_detected': [],
            'warnings': []
        }
        
        command_lower = command.lower()
        
        for threat_category, patterns in self.threat_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command_lower):
                    threat_results['threats_detected'].append({
                        'category': threat_category,
                        'pattern': pattern,
                        'severity': self._get_threat_severity(threat_category)
                    })
                    
                    # Increase risk score based on threat category
                    if threat_category == 'system_commands':
                        threat_results['risk_score'] += 40
                        threat_results['threat_level'] = ThreatLevel.CRITICAL
                    elif threat_category == 'privilege_escalation':
                        threat_results['risk_score'] += 35
                        threat_results['threat_level'] = ThreatLevel.HIGH
                    elif threat_category == 'persistence':
                        threat_results['risk_score'] += 30
                        threat_results['threat_level'] = ThreatLevel.HIGH
                    elif threat_category == 'network_exposure':
                        threat_results['risk_score'] += 25
                        threat_results['threat_level'] = ThreatLevel.MEDIUM
                    elif threat_category == 'data_exfiltration':
                        threat_results['risk_score'] += 20
                        threat_results['threat_level'] = ThreatLevel.MEDIUM
        
        return threat_results
    
    def _validate_module_usage(self, command: str) -> Dict[str, Any]:
        """Validate module usage command."""
        module_results = {
            'module_warnings': [],
            'module_recommendations': []
        }
        
        # Extract module path
        module_match = re.search(r'use\s+(\S+)', command)
        if module_match:
            module_path = module_match.group(1)
            
            # Check for dangerous modules
            dangerous_modules = [
                'exploit/multi/misc/java_jdwp_debugger',
                'exploit/windows/smb/ms17_010_eternalblue',
                'post/windows/gather/hashdump'
            ]
            
            for dangerous in dangerous_modules:
                if module_path == dangerous:
                    module_results['module_warnings'].append(
                        f"High-impact module detected: {module_path}"
                    )
                    module_results['module_recommendations'].append(
                        "Ensure proper authorization before using this module"
                    )
            
            # Check module category
            if '/local/' in module_path:
                module_results['module_warnings'].append(
                    "Local exploit module - ensure target system authorization"
                )
            
            if '/gather/' in module_path:
                module_results['module_warnings'].append(
                    "Information gathering module - respect privacy and legal requirements"
                )
        
        return module_results
    
    def _get_threat_severity(self, threat_category: str) -> str:
        """Get severity level for threat category."""
        severity_map = {
            'system_commands': 'critical',
            'privilege_escalation': 'high',
            'persistence': 'high',
            'network_exposure': 'medium',
            'data_exfiltration': 'medium'
        }
        return severity_map.get(threat_category, 'low')
    
    async def _log_security_event(self, action_type: ActionType, threat_level: ThreatLevel, 
                                  command: str, context: Dict[str, Any], 
                                  blocked: bool = False, risk_score: int = 0):
        """Log security event for audit trail."""
        event = SecurityEvent(
            timestamp=time.time(),
            action_type=action_type,
            threat_level=threat_level,
            user_context=context.get('user', 'unknown'),
            command=command,
            details=context,
            blocked=blocked,
            risk_score=risk_score
        )
        
        self.security_events.append(event)
        
        # Keep only recent events in memory (last 1000)
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]
        
        # Log to audit file
        if self.policy.enable_audit_logging:
            audit_entry = {
                'timestamp': event.timestamp,
                'action': event.action_type.value,
                'threat_level': event.threat_level.value,
                'command': command[:100],  # Truncate for log
                'blocked': blocked,
                'risk_score': risk_score,
                'context': context
            }
            
            self.audit_logger.info(json.dumps(audit_entry))
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get security summary and statistics."""
        recent_events = [e for e in self.security_events if (time.time() - e.timestamp) < 3600]
        
        threat_counts = {}
        for event in recent_events:
            threat_level = event.threat_level.value
            threat_counts[threat_level] = threat_counts.get(threat_level, 0) + 1
        
        return {
            'total_events': len(self.security_events),
            'recent_events_1h': len(recent_events),
            'threat_level_counts': threat_counts,
            'blocked_commands': len([e for e in recent_events if e.blocked]),
            'average_risk_score': sum(e.risk_score for e in recent_events) / len(recent_events) if recent_events else 0,
            'active_sessions': len(self.active_sessions),
            'policy_settings': {
                'max_command_length': self.policy.max_command_length,
                'max_concurrent_sessions': self.policy.max_concurrent_sessions,
                'audit_logging_enabled': self.policy.enable_audit_logging
            }
        }
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions."""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_info in self.active_sessions.items():
            if (current_time - session_info['last_activity']) > self.policy.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            logger.info(f"Cleaned up expired session: {session_id}")
        
        return len(expired_sessions)