#!/usr/bin/env python3

"""
Improved Metasploit Framework Console MCP
-----------------------------------------
This module integrates Metasploit Framework with MCP using improved execution strategies
for better reliability and error handling.
"""

import os
import sys
import logging
import subprocess
import asyncio
import json
import shutil
from typing import Dict, Any, Optional

# Set up logging with configurable handlers
logger = logging.getLogger("msfconsole_mcp")
logger.setLevel(logging.INFO)

# Create formatters
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create file handler - always used
file_handler = logging.FileHandler("msfconsole_mcp_improved.log")
file_handler.setFormatter(log_format)
logger.addHandler(file_handler)

# Process command line arguments
import argparse
parser = argparse.ArgumentParser(description="Improved Metasploit MCP Server")
parser.add_argument("--json-stdout", action="store_true", help="Ensure all stdout is valid JSON")
parser.add_argument("--strict-mode", action="store_true", help="Run in strict JSON mode")
parser.add_argument("--debug-to-stderr", action="store_true", help="Redirect debug output to stderr")
args = parser.parse_args()

# Configure JSON handling
json_stdout = args.json_stdout or "MCP_JSON_STDOUT" in os.environ
strict_mode = args.strict_mode or "MCP_STRICT_MODE" in os.environ
debug_to_stderr = args.debug_to_stderr or "MCP_DEBUG_TO_STDERR" in os.environ

# Configure JSON filtering if enabled
if json_stdout or strict_mode:
    try:
        from json_filter import install_json_filter
        json_filter = install_json_filter(debug=True)
        logger.info(f"JSON filtering enabled for stdout (strict mode: {strict_mode})")
    except ImportError as e:
        logger.warning(f"Could not import json_filter module: {e}")
        logger.warning("JSON filtering disabled - protocol errors may occur")

# Configure log handlers based on settings
if debug_to_stderr:
    # Add stderr handler if requested
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(log_format)
    logger.addHandler(stderr_handler)
    logger.info("Debug output redirected to stderr")
elif not json_stdout and not strict_mode:
    # Add stdout handler only if not in JSON mode
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(log_format)
    logger.addHandler(stdout_handler)
    logger.info("Debug output directed to stdout (may interfere with MCP protocol)")
