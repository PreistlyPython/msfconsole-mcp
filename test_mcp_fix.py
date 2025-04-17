#!/usr/bin/env python3

"""
Test script to verify our MCP fixes
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import our modules with better error handling
try:
    # Try to import the safe_context module first since it's critical
    from safe_context import SafeContext
    logger.info("Successfully imported SafeContext")
except ImportError as e:
    logger.error(f"Failed to import SafeContext: {e}")
    sys.exit(1)

try:
    # Import FastMCP and Context
    from mcp.server.fastmcp import FastMCP, Context
    logger.info("Successfully imported FastMCP and Context")
except ImportError as e:
    logger.error(f"Failed to import MCP modules: {e}")
    sys.exit(1)

# Create test functions

async def test_report_progress():
    """Test report_progress function"""
    print("\n=== Testing report_progress ===")
    
    # Create a dummy Context
    class DummyContext:
        async def report_progress(self, *args, **kwargs):
            print(f"report_progress called with args={args}, kwargs={kwargs}")
            return True
    
    # Test SafeContext with different argument patterns
    ctx = SafeContext(DummyContext())
    
    # Test with 2 args
    print("Testing with 2 args...")
    await ctx.report_progress(50, 100)
    
    # Test with 3 args
    print("Testing with 3 args...")
    await ctx.report_progress(50, 100, "Testing progress")
    
    print("report_progress test completed")

async def test_check_metasploit():
    """Test Metasploit checker"""
    print("\n=== Testing Metasploit Checker ===")
    
    # Only import if installed
    try:
        from check_metasploit import MetasploitChecker
        checker = MetasploitChecker(timeout=10)
        installed, msg = await checker.check_installation()
        print(f"Metasploit installed: {installed}")
        print(f"Installation message: {msg}")
        
        if installed:
            print("Testing version check...")
            version_result = await checker.get_version()
            print(f"Version check result: {version_result}")
    except ImportError:
        print("check_metasploit module not found, skipping test")

async def main():
    """Main function to run all tests"""
    print("Starting test suite for MCP fixes...")
    
    try:
        # Test report_progress function
        await test_report_progress()
        
        # Test Metasploit checker
        await test_check_metasploit()
        
        print("\nAll tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\nTest failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
