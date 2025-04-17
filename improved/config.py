#!/usr/bin/env python3

"""
Configuration settings for the Metasploit Framework Console MCP
"""

import os
import shutil
import logging

logger = logging.getLogger(__name__)

# Find msfconsole and msfvenom paths
msfconsole_path = shutil.which("msfconsole") or "/usr/bin/msfconsole"
msfvenom_path = shutil.which("msfvenom") or "/usr/bin/msfvenom"

# Check if files exist
if not os.path.exists(msfconsole_path):
    logger.warning(f"msfconsole not found at {msfconsole_path}")
    
if not os.path.exists(msfvenom_path):
    logger.warning(f"msfvenom not found at {msfvenom_path}")

# Configuration settings
CONFIG = {
    # Metasploit Framework settings
    "metasploit": {
        "msfconsole_path": msfconsole_path,
        "msfvenom_path": msfvenom_path,
        "workspace": "default",  # Default Metasploit workspace
        "database_timeout": 15,  # Seconds to wait for database operations
    },
    
    # Security settings
    "security": {
        "command_timeout": 45,  # Maximum time (seconds) a command can run
        "disallowed_modules": [
            # Add dangerous modules that should be blocked
            # Examples:
            # "exploit/windows/browser/",  # Browser exploits can be dangerous
            # "post/windows/gather/credentials",  # Credential gathering can be sensitive
        ],
        "validate_commands": True,  # Whether to validate commands before running
        "allowed_commands": [
            # Basic commands
            "help", "version", "info", "use", "show", "search", "exit", "quit",
            # Database commands
            "db_status", "db_connect", "workspace", "hosts", "services", "vulns", "notes", "loot", "creds",
            # Module commands
            "back", "set", "setg", "unset", "unsetg", "run", "exploit", "check", "reload", "options",
            # Session commands
            "sessions", "background",
            # Scan commands
            "analyze", "db_nmap", "db_import",
        ],
    },
    
    # Output settings
    "output": {
        "max_output_length": 50000,  # Maximum length of command output to return
        "truncation_message": "\n[... Output truncated due to length ...]",
    },
    
    # Performance settings
    "performance": {
        "use_resource_scripts": True,  # Use resource scripts for command batching
        "cleanup_temp_files": True,  # Clean up temporary files after execution
    },
}

# Python compatibility fixes
PY_COMPATIBILITY_FIXES = {
    "asyncio_fix": True,  # Enable fixes for asyncio in Python 3.11+
    "type_annotations": True,  # Enable compatibility for type annotations
}