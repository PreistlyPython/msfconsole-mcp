#!/usr/bin/env python3

"""
Test suite for SafeContext implementation.

This script tests the SafeContext wrapper against multiple mock implementations
of MCP Context interfaces to verify compatibility with different SDK versions.
"""

import asyncio
import inspect
import logging
from typing import List, Dict, Any, Optional, Union

from safe_context import SafeContext

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define mock Context classes for different MCP API versions

class MCPContext_v1:
    """Mock implementation of early MCP Context API"""
    
    async def report_progress(self, current, total):
        """Early MCP SDK version with 2 parameters"""
        print(f"MCPContext_v1.report_progress({current}, {total})")
        return True
    
    async def info(self, message):
        """Log an info message"""
        print(f"MCPContext_v1.info: {message}")
        return True
    
    async def error(self, message):
        """Log an error message"""
        print(f"MCPContext_v1.error: {message}")
        return True


class MCPContext_v2:
    """Mock implementation of newer MCP Context API"""
    
    async def report_progress(self, current, total, message):
        """Newer MCP SDK version with 3 parameters"""
        print(f"MCPContext_v2.report_progress({current}, {total}, '{message}')")
        return True
    
    async def info(self, message):
        """Log an info message"""
        print(f"MCPContext_v2.info: {message}")
        return True
    
    async def error(self, message):
        """Log an error message"""
        print(f"MCPContext_v2.error: {message}")
        return True
    
    async def warning(self, message):
        """Log a warning message"""
        print(f"MCPContext_v2.warning: {message}")
        return True


class MCPContext_v3:
    """Mock implementation of different style MCP Context API"""
    
    async def progress(self, message, percentage):
        """Alternative progress reporting style"""
        print(f"MCPContext_v3.progress('{message}', {percentage})")
        return True
    
    async def send_info(self, message):
        """Alternative info style"""
        print(f"MCPContext_v3.send_info: {message}")
        return True
    
    async def send_error(self, message):
        """Alternative error style"""
        print(f"MCPContext_v3.send_error: {message}")
        return True


class MCPContext_Broken:
    """Mock implementation with methods that raise exceptions"""
    
    async def report_progress(self, current, total):
        """Broken implementation that raises an exception"""
        raise RuntimeError("Simulated error in report_progress")
    
    async def info(self, message):
        """Broken implementation that raises an exception"""
        raise RuntimeError("Simulated error in info")


async def test_report_progress_v1():
    """Test with MCP Context v1 (2 parameters)"""
    print("\n=== Testing with MCP Context v1 (2 parameters) ===")
    
    ctx = MCPContext_v1()
    safe_ctx = SafeContext(ctx)
    
    # Verify the signature detection
    sig = inspect.signature(ctx.report_progress)
    print(f"Original signature: {sig} with {len(sig.parameters)} parameters")
    
    # Test basic progress reporting
    await safe_ctx.report_progress(30, 100, "Test message")
    
    # Test percentage calculation and normalization
    await safe_ctx.report_progress(30, 0, "Division by zero test")
    await safe_ctx.report_progress(-10, 100, "Negative value test")
    await safe_ctx.report_progress(200, 100, "Value > 100% test")
    
    # Test the progress wrapper method
    await safe_ctx.progress("Progress message", 50)
    
    print("All v1 tests passed!")
    return True


async def test_report_progress_v2():
    """Test with MCP Context v2 (3 parameters)"""
    print("\n=== Testing with MCP Context v2 (3 parameters) ===")
    
    ctx = MCPContext_v2()
    safe_ctx = SafeContext(ctx)
    
    # Verify the signature detection
    sig = inspect.signature(ctx.report_progress)
    print(f"Original signature: {sig} with {len(sig.parameters)} parameters")
    
    # Test basic progress reporting
    await safe_ctx.report_progress(30, 100, "Test message")
    
    # Test with empty message
    await safe_ctx.report_progress(60, 100, "")
    
    # Test with None message (should be handled gracefully)
    await safe_ctx.report_progress(60, 100)
    
    # Test the progress wrapper method
    await safe_ctx.progress("Progress message", 50)
    
    print("All v2 tests passed!")
    return True


async def test_alternative_style():
    """Test with alternative MCP Context style (progress method)"""
    print("\n=== Testing with alternative MCP Context style ===")
    
    ctx = MCPContext_v3()
    safe_ctx = SafeContext(ctx)
    
    # Test the progress method directly
    await safe_ctx.progress("Direct progress call", 75)
    
    # Test through report_progress
    await safe_ctx.report_progress(30, 40, "Via report_progress")
    
    print("All alternative style tests passed!")
    return True


async def test_error_handling():
    """Test with broken MCP Context implementation"""
    print("\n=== Testing error handling with broken Context ===")
    
    ctx = MCPContext_Broken()
    safe_ctx = SafeContext(ctx)
    
    # These should not raise exceptions but log errors
    await safe_ctx.report_progress(50, 100, "Should handle errors")
    await safe_ctx.info("Info with error handling")
    
    print("All error handling tests passed!")
    return True


async def test_null_context():
    """Test with null context (should use logger fallback)"""
    print("\n=== Testing with null context ===")
    
    safe_ctx = SafeContext(None)
    
    # These should fall back to logger
    await safe_ctx.report_progress(50, 100, "Using logger fallback")
    await safe_ctx.info("Info via logger")
    await safe_ctx.error("Error via logger")
    await safe_ctx.warning("Warning via logger")
    await safe_ctx.progress("Progress via logger", 25)
    
    print("All null context tests passed!")
    return True


async def test_message_methods():
    """Test message logging methods across different Context styles"""
    print("\n=== Testing message methods ===")
    
    # Test with v1
    ctx1 = MCPContext_v1()
    safe_ctx1 = SafeContext(ctx1)
    await safe_ctx1.info("Info message v1")
    await safe_ctx1.error("Error message v1")
    await safe_ctx1.warning("Warning message v1")  # Should fall back to logger
    
    # Test with v2
    ctx2 = MCPContext_v2()
    safe_ctx2 = SafeContext(ctx2)
    await safe_ctx2.info("Info message v2")
    await safe_ctx2.error("Error message v2")
    await safe_ctx2.warning("Warning message v2")
    
    # Test with v3
    ctx3 = MCPContext_v3()
    safe_ctx3 = SafeContext(ctx3)
    await safe_ctx3.info("Info message v3")
    await safe_ctx3.error("Error message v3")
    await safe_ctx3.warning("Warning message v3")  # Should fall back to logger
    
    print("All message method tests passed!")
    return True


async def main():
    """Run all tests sequentially"""
    print("=== Starting SafeContext Tests ===")
    
    await test_report_progress_v1()
    await test_report_progress_v2()
    await test_alternative_style()
    await test_error_handling()
    await test_null_context()
    await test_message_methods()
    
    print("\n=== All tests completed successfully! ===")


if __name__ == "__main__":
    asyncio.run(main())
