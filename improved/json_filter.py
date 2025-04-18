#!/usr/bin/env python3

"""
JSON Filter for MCP
------------------
This module provides JSON filtering for MCP server stdout to ensure
only valid JSON-RPC 2.0 messages are sent.
"""

import sys
import json
import logging
from typing import Optional, Dict, Any

# Get logger
logger = logging.getLogger("msfconsole_mcp")

def is_valid_jsonrpc(obj: Dict[str, Any], strict: bool = False) -> bool:
    """
    Check if an object is a valid JSON-RPC 2.0 message.
    
    Args:
        obj: Object to check
        strict: If True, require jsonrpc field to be "2.0"
    
    Returns:
        True if valid JSON-RPC, False otherwise
    """
    if not isinstance(obj, dict):
        return False
    
    if strict:
        # Strict mode: must have jsonrpc field with value "2.0"
        if not ("jsonrpc" in obj and obj["jsonrpc"] == "2.0"):
            return False
        
        # Must have either method (request) or result/error (response)
        if "method" not in obj and "result" not in obj and "error" not in obj:
            return False
    else:
        # Less strict: at least must be a JSON object
        pass
    
    return True

class JSONFilter:
    """
    Filter for ensuring stdout only contains valid JSON-RPC 2.0 messages.
    """
    
    def __init__(self, strict: bool = False, debug: bool = False):
        """
        Initialize JSON filter.
        
        Args:
            strict: If True, require strict JSON-RPC 2.0 compliance
            debug: If True, enable debug logging
        """
        self.strict = strict
        self.debug = debug
        self.stdout = sys.stdout
        logger.info(f"JSON filter initialized (strict mode - only JSON-RPC 2.0 messages allowed)")
        
        if self.debug:
            logger.debug("JSON filter debug logging enabled")
    
    def write(self, data: str):
        """
        Filter and write data to stdout.
        
        Args:
            data: Data to write
        """
        # Skip empty lines
        if not data.strip():
            return
        
        # Try to parse as JSON
        try:
            obj = json.loads(data)
            
            # Check if valid JSON-RPC
            if is_valid_jsonrpc(obj, self.strict):
                # Valid JSON-RPC message
                self.stdout.write(data)
                self.stdout.flush()
            else:
                # Valid JSON but not a JSON-RPC message
                logger.warning(f"Filtered non-RPC JSON: {data[:50]}...")
        except json.JSONDecodeError:
            # Not valid JSON
            logger.warning(f"Filtered invalid JSON: {data[:50]}...")
    
    def flush(self):
        """Flush the underlying stdout."""
        self.stdout.flush()

def install_json_filter(strict: bool = False, debug: bool = False) -> JSONFilter:
    """
    Install JSON filter for stdout.
    
    Args:
        strict: If True, require strict JSON-RPC 2.0 compliance
        debug: If True, enable debug logging
    
    Returns:
        Installed JSONFilter instance
    """
    # Create filter instance
    json_filter = JSONFilter(strict=strict, debug=debug)
    
    # Replace sys.stdout
    sys.stdout = json_filter
    
    logger.info(f"JSON filtering enabled for stdout (strict: {strict}, debug: {debug})")
    
    return json_filter
