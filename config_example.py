#!/usr/bin/env python3

"""
Example configuration file for MSFConsole MCP.
Rename this to 'config.py' and modify as needed.
"""

# Metasploit configuration
metasploit = {
    # Path to msfconsole (leave empty to use system path)
    "msfconsole_path": "",
    
    # Path to msfvenom (leave empty to use system path)
    "msfvenom_path": "",
    
    # Whether to use the Metasploit database
    "msf_database": True,
    
    # Default workspace
    "workspace": "default",
    
    # Default local host for payloads
    "lhost": "0.0.0.0",
    
    # Default local port for payloads
    "lport": "4444"
}

# Output configuration
output = {
    # Maximum length of output to return
    "max_output_length": 10000,
    
    # Message shown when output is truncated
    "truncation_message": "\n[...Output truncated due to length...]"
}

# Security configuration
security = {
    # Allowed module types
    "allowed_modules": ["auxiliary/", "exploit/", "post/", "payload/", "encoder/", "nop/"],
    
    # Specifically disallowed modules
    "disallowed_modules": [],
    
    # Timeout for commands in seconds
    "command_timeout": 300
}
