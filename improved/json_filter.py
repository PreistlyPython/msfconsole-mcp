#!/usr/bin/env python3

"""
Improved JSON Filter Module for MCP
----------------------------------
Ensures that only valid JSON-RPC 2.0 messages are output to stdout,
which is required for MCP protocol compliance.

This module acts as a filtering layer that intercepts all stdout writes and:
1. Only allows valid JSON to pass through
2. In strict mode, only allows valid JSON-RPC 2.0 messages to pass through
3. Redirects all other output to stderr

Usage:
    from json_filter import install_json_filter
    
    # Basic usage - filter any non-JSON output
    json_filter = install_json_filter()
    
    # Enable debug logging and strict mode (only JSON-RPC 2.0 messages)
    json_filter = install_json_filter(debug=True, strict=True)
"""

import sys
import json
import logging
import re
from typing import Any, TextIO, Optional, Dict, Union

# Configure logging
logger = logging.getLogger("json_filter")
logger.setLevel(logging.INFO)

class JSONFilteredStdout:
    """
    A stdout wrapper that only allows valid JSON or JSON-RPC to pass through.
    All other output is redirected to stderr or discarded.
    """
    
    def __init__(self, 
                 original_stdout: TextIO = sys.stdout, 
                 debug: bool = False,
                 strict: bool = False,
                 log_filtered: bool = True):
        """
        Initialize the JSON filter.
        
        Args:
            original_stdout: The original stdout to wrap
            debug: Enable debug logging
            strict: Only allow valid JSON-RPC 2.0 messages in strict mode
            log_filtered: Log filtered (non-JSON) output to stderr
        """
        self.original_stdout = original_stdout
        self.debug = debug
        self.strict = strict
        self.log_filtered = log_filtered
        self.buffer = ""
        self.logger = logger
        
        # Setup logging to stderr
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
            logger.addHandler(handler)
            
        if debug:
            logger.setLevel(logging.DEBUG)
            logger.debug("JSON filter debug logging enabled")
            
        msg = "JSON filter initialized"
        if strict:
            msg += " (strict mode - only JSON-RPC 2.0 messages allowed)"
        logger.info(msg)
    
    def is_valid_jsonrpc(self, obj: Dict[str, Any]) -> bool:
        """
        Check if an object is a valid JSON-RPC 2.0 message.
        
        Args:
            obj: The parsed JSON object
            
        Returns:
            True if it's a valid JSON-RPC 2.0 message, False otherwise
        """
        # Must have jsonrpc field with value "2.0"
        if not isinstance(obj, dict) or obj.get("jsonrpc") != "2.0":
            return False
        
        # Check if it's a request (must have method and id)
        if "method" in obj and "id" in obj:
            return True
        
        # Check if it's a notification (must have method, must not have id)
        if "method" in obj and "id" not in obj:
            return True
        
        # Check if it's a response (must have id and either result or error)
        if "id" in obj and ("result" in obj or "error" in obj):
            return True
            
        # Not a valid JSON-RPC message
        return False
    
    def write(self, text: str) -> int:
        """
        Filter and write only valid JSON or JSON-RPC to stdout.
        Other output is redirected to stderr or discarded.
        
        Args:
            text: The text to write
            
        Returns:
            Number of characters written
        """
        if not text:
            return 0
            
        # Skip empty lines
        if text.strip() == "":
            return len(text)
        
        # First try to parse as JSON
        try:
            obj = json.loads(text)
            
            # In strict mode, verify it's a valid JSON-RPC message
            if self.strict and not self.is_valid_jsonrpc(obj):
                if self.debug:
                    logger.debug(f"Filtered non-JSON-RPC JSON: {text[:50]}...")
                
                if self.log_filtered:
                    # Log filtered output to stderr
                    sys.stderr.write(f"[JSON-FILTER] Non-JSON-RPC output: {text[:100]}...\n")
                    sys.stderr.flush()
                
                return len(text)
            
            # It's valid JSON (and valid JSON-RPC in strict mode)
            bytes_written = self.original_stdout.write(text)
            self.original_stdout.flush()
            
            if self.debug:
                if self.strict:
                    logger.debug(f"Passed valid JSON-RPC: {text[:50]}...")
                else:
                    logger.debug(f"Passed valid JSON: {text[:50]}...")
            
            return bytes_written
            
        except json.JSONDecodeError:
            # Not valid JSON, redirect to stderr or discard
            if self.debug:
                logger.debug(f"Filtered non-JSON: {text[:50]}...")
            
            if self.log_filtered:
                # Log filtered output to stderr
                sys.stderr.write(f"[JSON-FILTER] Non-JSON output: {text[:100]}...\n")
                sys.stderr.flush()
            
            return len(text)
    
    def flush(self):
        """Pass through flush calls to the original stdout."""
        self.original_stdout.flush()
        
    def isatty(self):
        """Pass through isatty calls to the original stdout."""
        return getattr(self.original_stdout, 'isatty', lambda: False)()

def install_json_filter(debug: bool = False, 
                        strict: bool = False,
                        log_filtered: bool = True) -> JSONFilteredStdout:
    """
    Install JSON filtering for stdout.
    
    Args:
        debug: Enable debug logging
        strict: Only allow valid JSON-RPC 2.0 messages in strict mode
        log_filtered: Log filtered (non-JSON) output to stderr
        
    Returns:
        The installed filter instance
    """
    # Create and configure filter
    json_filter = JSONFilteredStdout(
        sys.stdout, 
        debug=debug, 
        strict=strict,
        log_filtered=log_filtered
    )
    
    # Replace stdout
    sys.stdout = json_filter
    logger.info(f"JSON filtering enabled for stdout (strict: {strict}, debug: {debug})")
    
    return json_filter

if __name__ == "__main__":
    # Simple test when run directly
    filter = install_json_filter(debug=True, strict=True)
    
    # Test valid JSON-RPC
    print('{"jsonrpc": "2.0", "id": 1, "method": "test"}')
    
    # Test valid JSON but not JSON-RPC (should be filtered in strict mode)
    print('{"test": "This is valid JSON but not JSON-RPC"}')
    
    # Test invalid output
    print('This is not JSON and should be filtered')
    
    # Test another valid JSON-RPC
    print('{"jsonrpc": "2.0", "id": 2, "result": {"success": true}}')
