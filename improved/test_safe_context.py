#!/usr/bin/env python3

"""
Test the SafeContext class to ensure it correctly handles different MCP Context APIs.
"""

import asyncio
import logging
from unittest.mock import MagicMock, AsyncMock
from typing import List, Dict, Any

from safe_context import SafeContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ContextWithTwoParams:
    """Mock Context class with report_progress taking 2 parameters"""
    async def report_progress(self, current, total):
        print(f"ContextWithTwoParams.report_progress({current}, {total})")
        return True


class ContextWithThreeParams:
    """Mock Context class with report_progress taking 3 parameters"""
    async def report_progress(self, current, total, message):
        print(f"ContextWithThreeParams.report_progress({current}, {total}, '{message}')")
        return True


async def test_report_progress():
    """Test the report_progress method with different context implementations"""
    
    # Test with two-parameter context
    ctx2 = ContextWithTwoParams()
    safe_ctx2 = SafeContext(ctx2)
    
    # Create a spy on the report_progress method
    original_method2 = ctx2.report_progress
    calls2 = []
    
    async def spy_method2(current, total):
        calls2.append((current, total))
        return await original_method2(current, total)
    
    ctx2.report_progress = spy_method2
    
    # Call with different parameter combinations
    await safe_ctx2.report_progress(30, 100, "Test message")
    await safe_ctx2.progress("Progress message", 50)
    
    print(f"Calls to context with 2 params: {calls2}")
    assert len(calls2) == 2, f"Expected 2 calls, got {len(calls2)}"
    assert calls2[0] == (30, 100), f"Expected (30, 100), got {calls2[0]}"
    assert calls2[1] == (50, 100), f"Expected (50, 100), got {calls2[1]}"
    
    # Test with three-parameter context
    ctx3 = ContextWithThreeParams()
    safe_ctx3 = SafeContext(ctx3)
    
    # Create a spy on the report_progress method
    original_method3 = ctx3.report_progress
    calls3 = []
    
    async def spy_method3(current, total, message):
        calls3.append((current, total, message))
        return await original_method3(current, total, message)
    
    ctx3.report_progress = spy_method3
    
    # Call with different parameter combinations
    await safe_ctx3.report_progress(30, 100, "Test message")
    await safe_ctx3.progress("Progress message", 50)
    
    print(f"Calls to context with 3 params: {calls3}")
    assert len(calls3) == 2, f"Expected 2 calls, got {len(calls3)}"
    assert calls3[0] == (30, 100, "Test message"), f"Expected (30, 100, 'Test message'), got {calls3[0]}"
    assert calls3[1] == (50, 100, "Progress message"), f"Expected (50, 100, 'Progress message'), got {calls3[1]}"
    
    print("All tests passed!")
    return True


async def test_other_methods():
    """Test other context methods with different implementations"""
    
    # Test info, error, warning methods
    ctx = MagicMock()
    ctx.info = AsyncMock()
    ctx.error = AsyncMock()
    ctx.warning = AsyncMock()
    
    safe_ctx = SafeContext(ctx)
    
    await safe_ctx.info("Info message")
    await safe_ctx.error("Error message")
    await safe_ctx.warning("Warning message")
    
    ctx.info.assert_called_once_with("Info message")
    ctx.error.assert_called_once_with("Error message")
    ctx.warning.assert_called_once_with("Warning message")
    
    print("All method tests passed!")
    return True


async def main():
    """Run all tests"""
    print("Testing SafeContext implementation...")
    
    await test_report_progress()
    await test_other_methods()
    
    print("All tests completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
