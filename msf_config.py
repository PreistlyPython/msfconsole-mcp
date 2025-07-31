#!/usr/bin/env python3

"""
MSF MCP Configuration Management
--------------------------------
Centralized configuration management with environment-specific settings,
performance tuning, and runtime configuration updates.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

@dataclass
class RPCSettings:
    host: str = "127.0.0.1"
    port: int = 55552
    username: str = "msf"
    password: str = "msf123"
    ssl: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5
    enable_compression: bool = True
    connection_pool_size: int = 10

@dataclass
class SecuritySettings:
    max_command_length: int = 1000
    command_timeout: int = 300  # 5 minutes for complex operations
    session_timeout: int = 3600
    max_concurrent_sessions: int = 10
    enable_audit_logging: bool = True
    blocked_keywords: List[str] = field(default_factory=lambda: [
        'rm -rf', 'format', 'fdisk', 'dd if=', 'shutdown', 'reboot'
    ])
    allowed_modules: List[str] = field(default_factory=lambda: [
        'auxiliary/', 'exploit/', 'payload/', 'encoder/', 'nop/', 'post/'
    ])
    require_workspace_isolation: bool = True
    enable_threat_detection: bool = True

@dataclass
class PerformanceSettings:
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutes
    cache_max_size: int = 1000
    batch_processing: bool = True
    max_batch_size: int = 50
    connection_pooling: bool = True
    async_operations: bool = True
    result_streaming: bool = True
    compression_enabled: bool = True
    memory_limit_mb: int = 512

@dataclass
class LoggingSettings:
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: str = "msfconsole_mcp_enhanced.log"
    max_file_size_mb: int = 100
    backup_count: int = 5
    audit_log_enabled: bool = True
    audit_log_path: str = "msf_security_audit.log"

@dataclass
class MetasploitPaths:
    msfconsole: str = "/usr/bin/msfconsole"
    msfvenom: str = "/usr/bin/msfvenom"
    msfrpcd: str = "/usr/bin/msfrpcd"
    workspace_directory: str = "/tmp/msf_workspaces"
    resource_scripts_directory: str = "/tmp/msf_scripts"

@dataclass
class MSFMCPConfig:
    environment: Environment = Environment.DEVELOPMENT
    rpc: RPCSettings = field(default_factory=RPCSettings)
    security: SecuritySettings = field(default_factory=SecuritySettings)
    performance: PerformanceSettings = field(default_factory=PerformanceSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    paths: MetasploitPaths = field(default_factory=MetasploitPaths)
    custom_settings: Dict[str, Any] = field(default_factory=dict)

class ConfigurationManager:
    """
    Manages configuration for MSF MCP with environment-specific settings,
    runtime updates, and validation.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or "msf_mcp_config.yaml"
        self.config: MSFMCPConfig = MSFMCPConfig()
        self._config_watchers = []
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file and environment variables."""
        # Load from file if it exists
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    if config_path.suffix.lower() == '.yaml' or config_path.suffix.lower() == '.yml':
                        config_data = yaml.safe_load(f)
                    else:
                        config_data = json.load(f)
                
                self._apply_config_data(config_data)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration file: {e}")
        else:
            logger.info("No configuration file found, using defaults")
        
        # Override with environment variables
        self._load_environment_variables()
        
        # Apply environment-specific settings
        self._apply_environment_settings()
        
        # Validate configuration
        self._validate_configuration()
    
    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to config object."""
        if 'environment' in config_data:
            self.config.environment = Environment(config_data['environment'])
        
        # Apply RPC settings
        if 'rpc' in config_data:
            rpc_data = config_data['rpc']
            for key, value in rpc_data.items():
                if hasattr(self.config.rpc, key):
                    setattr(self.config.rpc, key, value)
        
        # Apply security settings
        if 'security' in config_data:
            security_data = config_data['security']
            for key, value in security_data.items():
                if hasattr(self.config.security, key):
                    setattr(self.config.security, key, value)
        
        # Apply performance settings
        if 'performance' in config_data:
            perf_data = config_data['performance']
            for key, value in perf_data.items():
                if hasattr(self.config.performance, key):
                    setattr(self.config.performance, key, value)
        
        # Apply logging settings
        if 'logging' in config_data:
            log_data = config_data['logging']
            for key, value in log_data.items():
                if hasattr(self.config.logging, key):
                    setattr(self.config.logging, key, value)
        
        # Apply path settings
        if 'paths' in config_data:
            path_data = config_data['paths']
            for key, value in path_data.items():
                if hasattr(self.config.paths, key):
                    setattr(self.config.paths, key, value)
        
        # Apply custom settings
        if 'custom' in config_data:
            self.config.custom_settings.update(config_data['custom'])
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'MSF_MCP_ENVIRONMENT': ('environment', lambda x: Environment(x)),
            'MSF_RPC_HOST': ('rpc.host', str),
            'MSF_RPC_PORT': ('rpc.port', int),
            'MSF_RPC_USERNAME': ('rpc.username', str),
            'MSF_RPC_PASSWORD': ('rpc.password', str),
            'MSF_RPC_SSL': ('rpc.ssl', lambda x: x.lower() == 'true'),
            'MSF_SECURITY_MAX_COMMAND_LENGTH': ('security.max_command_length', int),
            'MSF_SECURITY_COMMAND_TIMEOUT': ('security.command_timeout', int),
            'MSF_SECURITY_AUDIT_LOGGING': ('security.enable_audit_logging', lambda x: x.lower() == 'true'),
            'MSF_PERFORMANCE_CACHE_ENABLED': ('performance.cache_enabled', lambda x: x.lower() == 'true'),
            'MSF_PERFORMANCE_BATCH_SIZE': ('performance.max_batch_size', int),
            'MSF_LOG_LEVEL': ('logging.level', str),
            'MSF_CONSOLE_PATH': ('paths.msfconsole', str),
            'MSF_VENOM_PATH': ('paths.msfvenom', str),
        }
        
        for env_var, (config_path, converter) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                try:
                    converted_value = converter(value)
                    self._set_nested_config(config_path, converted_value)
                    logger.debug(f"Set {config_path} from environment: {converted_value}")
                except Exception as e:
                    logger.error(f"Error converting environment variable {env_var}: {e}")
    
    def _set_nested_config(self, path: str, value: Any):
        """Set nested configuration value using dot notation."""
        parts = path.split('.')
        obj = self.config
        
        for part in parts[:-1]:
            obj = getattr(obj, part)
        
        setattr(obj, parts[-1], value)
    
    def _apply_environment_settings(self):
        """Apply environment-specific configuration overrides."""
        env = self.config.environment
        
        if env == Environment.DEVELOPMENT:
            # Development settings
            self.config.logging.level = "DEBUG"
            self.config.security.enable_audit_logging = True
            self.config.performance.cache_enabled = False  # Disable cache for development
            self.config.rpc.timeout = 60  # Longer timeout for debugging
        
        elif env == Environment.TESTING:
            # Testing settings
            self.config.logging.level = "INFO"
            self.config.security.max_concurrent_sessions = 5
            self.config.performance.cache_ttl = 60  # Short cache for testing
            self.config.rpc.max_retries = 1  # Fast failure for tests
        
        elif env == Environment.PRODUCTION:
            # Production settings
            self.config.logging.level = "WARNING"
            self.config.security.enable_audit_logging = True
            self.config.security.require_workspace_isolation = True
            self.config.performance.cache_enabled = True
            self.config.performance.connection_pooling = True
            self.config.rpc.enable_compression = True
    
    def _validate_configuration(self):
        """Validate configuration settings."""
        errors = []
        
        # Validate RPC settings
        if self.config.rpc.port < 1 or self.config.rpc.port > 65535:
            errors.append("RPC port must be between 1 and 65535")
        
        if self.config.rpc.timeout < 1:
            errors.append("RPC timeout must be positive")
        
        # Validate security settings
        if self.config.security.max_command_length < 10:
            errors.append("Max command length must be at least 10")
        
        if self.config.security.command_timeout < 1:
            errors.append("Command timeout must be positive")
        
        # Validate performance settings
        if self.config.performance.cache_ttl < 0:
            errors.append("Cache TTL cannot be negative")
        
        if self.config.performance.max_batch_size < 1:
            errors.append("Max batch size must be at least 1")
        
        # Validate paths
        required_paths = [
            ('msfconsole', self.config.paths.msfconsole),
            ('msfvenom', self.config.paths.msfvenom),
            ('msfrpcd', self.config.paths.msfrpcd)
        ]
        
        for name, path in required_paths:
            if not os.path.exists(path):
                logger.warning(f"{name} not found at {path}")
        
        if errors:
            error_msg = "Configuration validation errors: " + "; ".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validation passed")
    
    def save_configuration(self, file_path: Optional[str] = None):
        """Save current configuration to file."""
        save_path = file_path or self.config_file
        
        try:
            config_dict = asdict(self.config)
            # Convert enum to string
            config_dict['environment'] = self.config.environment.value
            
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise
    
    def update_setting(self, path: str, value: Any):
        """Update a configuration setting at runtime."""
        try:
            old_value = self._get_nested_config(path)
            self._set_nested_config(path, value)
            
            # Validate the change
            self._validate_configuration()
            
            logger.info(f"Updated {path}: {old_value} -> {value}")
            
            # Notify watchers
            for watcher in self._config_watchers:
                try:
                    watcher(path, old_value, value)
                except Exception as e:
                    logger.error(f"Error in config watcher: {e}")
        
        except Exception as e:
            logger.error(f"Error updating configuration {path}: {e}")
            raise
    
    def _get_nested_config(self, path: str) -> Any:
        """Get nested configuration value using dot notation."""
        parts = path.split('.')
        obj = self.config
        
        for part in parts:
            obj = getattr(obj, part)
        
        return obj
    
    def add_config_watcher(self, callback):
        """Add a callback to be notified of configuration changes."""
        self._config_watchers.append(callback)
    
    def get_config(self) -> MSFMCPConfig:
        """Get the current configuration."""
        return self.config
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        config_dict = asdict(self.config)
        config_dict['environment'] = self.config.environment.value
        return config_dict
    
    def reload_configuration(self):
        """Reload configuration from file."""
        logger.info("Reloading configuration...")
        self._load_configuration()
    
    def create_default_config_file(self, file_path: Optional[str] = None):
        """Create a default configuration file."""
        save_path = file_path or "msf_mcp_config_default.yaml"
        
        # Create default configuration
        default_config = MSFMCPConfig()
        
        # Add some example custom settings
        default_config.custom_settings = {
            "example_setting": "example_value",
            "feature_flags": {
                "experimental_features": False,
                "advanced_logging": True
            }
        }
        
        # Save as temporary config and then save to file
        temp_config = self.config
        self.config = default_config
        self.save_configuration(save_path)
        self.config = temp_config
        
        logger.info(f"Default configuration created at {save_path}")

# Global configuration manager instance
config_manager: Optional[ConfigurationManager] = None

def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager instance."""
    global config_manager
    if config_manager is None:
        config_manager = ConfigurationManager()
    return config_manager

def get_config() -> MSFMCPConfig:
    """Get the current configuration."""
    return get_config_manager().get_config()

def update_config(path: str, value: Any):
    """Update a configuration setting."""
    get_config_manager().update_setting(path, value)

def reload_config():
    """Reload configuration from file."""
    get_config_manager().reload_configuration()