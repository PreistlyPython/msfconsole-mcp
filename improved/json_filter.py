#!/usr/bin/env python3

"""
JSON Output Filter
-----------------
This module provides robust JSON filtering capabilities for the MCP protocol.
It ensures that only valid JSON is sent to stdout, which is essential for
maintaining protocol integrity.

Usage:
    from json_filter import SafeJsonStdout
    
    # Install the filter
    sys.stdout = SafeJsonStdout()
    
    # Use normally - only valid JSON will be sent to stdout
    print("{"command": "status"}") # Will be sent to stdout
    print("Starting up...") # Will be redirected to stderr
"""

import sys
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("json_filter")

class SafeJsonStdout:
    """
    A class that wraps stdout to ensure only valid JSON is written to it.
    Non-JSON output is redirected to stderr with appropriate logging.
    """
    
    def __init__(self, original_stdout=None):
        """
        Initialize the SafeJsonStdout with the original stdout stream.
        
        Args:
            original_stdout: The original stdout stream (defaults to sys.stdout)
        """
        self.original_stdout = original_stdout or sys.stdout
        self.buffer = ""
        self.json_count = 0
        self.filtered_count = 0
        logger.info("JSON filter initialized")
    
    def write(self, text):
        """
        Write text to stdout if it's valid JSON, otherwise to stderr.
        
        Args:
            text: The text to write
            
        Returns:
            The number of bytes written
        """
        # Skip empty content
        if not text or text.isspace():
            return 0
        
        try:
            # Try to parse as JSON
            json.loads(text)
            
            # Valid JSON, write to original stdout
            bytes_written = self.original_stdout.write(text)
            self.json_count += 1
            return bytes_written
        except json.JSONDecodeError:
            # Not valid JSON, log and redirect to stderr
            preview = text[:100] + "..." if len(text) > 100 else text
            logger.debug(f"Filtered non-JSON output: {preview.strip()}")
            print(preview, file=sys.stderr)
            self.filtered_count += 1
            return len(text)  # Pretend we wrote the full content
    
    def flush(self):
        """Flush the original stdout"""
        self.original_stdout.flush()
    
    def get_stats(self):
        """
        Return statistics about the filtering activity.
        
        Returns:
            A dictionary with filter statistics
        """
        return {
            "json_messages": self.json_count,
            "filtered_messages": self.filtered_count,
            "total_messages": self.json_count + self.filtered_count
        }


def install_json_filter(debug=False):
    """
    Install the JSON filter for stdout.
    
    Args:
        debug: Enable debug logging if True
        
    Returns:
        The installed SafeJsonStdout instance
    """
    if debug:
        logger.setLevel(logging.DEBUG)
    
    # Create and install the filter
    json_filter = SafeJsonStdout()
    sys.stdout = json_filter
    
    logger.info("JSON filtering enabled for stdout")
    return json_filter


if __name__ == "__main__":
    # Example usage
    json_filter = install_json_filter(debug=True)
    
    print("This is not JSON and will be filtered")
    print('{"message": "This is valid JSON and will pass through"}')
    print("Another non-JSON line that will be filtered")
    
    # Print statistics
    stats = json_filter.get_stats()
    logger.info(f"Filter stats: {stats}")
