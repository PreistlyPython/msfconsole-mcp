
# Enhanced timeout configuration for execute_msf_command
COMMAND_TIMEOUTS = {
    # Fast commands - basic status and help
    "help": 45,
    "db_status": 30,
    "workspace": 30,
    
    # Medium commands - information retrieval
    "version": 75,
    "show": 60,
    "info": 75,
    
    # Complex commands - operations and searches
    "search": 90,
    "use": 90,
    "exploit": 120,
    "generate": 90,
    
    # Default for unknown commands
    "default": 75
}

def get_adaptive_timeout(command: str) -> int:
    """Get adaptive timeout based on command type"""
    command_lower = command.lower().strip()
    
    # Check for specific command patterns
    for pattern, timeout in COMMAND_TIMEOUTS.items():
        if pattern in command_lower:
            return timeout
    
    # Default timeout
    return COMMAND_TIMEOUTS["default"]
