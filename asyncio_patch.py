#!/usr/bin/env python3

"""
AsyncIO Compatibility Patch for MSFConsole MCP
This module provides patches for asyncio compatibility issues in Python 3.12+
"""

import sys
import asyncio
import logging
import platform

logger = logging.getLogger(__name__)

def apply_patches():
    """
    Apply asyncio patches for different Python versions
    """
    version_info = platform.python_version_tuple()
    major, minor = int(version_info[0]), int(version_info[1])
    
    logger.info(f"Checking asyncio compatibility for Python {major}.{minor}")
    
    if major == 3 and minor >= 11:
        logger.warning(f"Python {major}.{minor} may have asyncio compatibility issues")
        
        # Apply compatibility patches for Python 3.11+
        _patch_asyncio_python311_plus()
        return True
        
    return False

def _patch_asyncio_python311_plus():
    """
    Apply asyncio patches for Python 3.11+
    """
    # Set a more lenient exception handler for asyncio
    loop = asyncio.get_event_loop()
    
    def custom_exception_handler(loop, context):
        """
        More lenient asyncio exception handler that avoids crashing the server
        on TaskGroup errors in Python 3.11+
        """
        exception = context.get('exception')
        if isinstance(exception, (asyncio.CancelledError, asyncio.TimeoutError)):
            # These exceptions are expected and can be safely ignored
            logger.debug(f"Ignoring expected asyncio exception: {exception}")
            return
            
        logger.error(f"Asyncio error: {context.get('message', '')}")
        if exception:
            logger.error(f"Exception: {exception}", exc_info=exception)
            
        # Don't propagate the exception, just log it
    
    # Apply the patched exception handler
    loop.set_exception_handler(custom_exception_handler)
    
    # Patch for TaskGroup issue in Python 3.11+
    if hasattr(asyncio, 'TaskGroup'):
        _patch_task_group()
    
    logger.info("Applied asyncio compatibility patches for Python 3.11+")

def _patch_task_group():
    """
    Patch TaskGroup to handle exceptions more gracefully
    """
    # We can't easily monkey patch the built-in TaskGroup class,
    # but we can provide a more tolerant version
    
    # Define a wrapper for create_task
    _original_create_task = asyncio.create_task
    
    def _patched_create_task(coro, *, name=None, context=None):
        """
        Create a task with better error handling
        """
        async def _wrapped_coro():
            try:
                return await coro
            except asyncio.CancelledError:
                # Simply propagate cancellation
                raise
            except Exception as e:
                # Log but don't crash the server
                logger.error(f"Task error in {name}: {e}", exc_info=True)
                return None
        
        return _original_create_task(_wrapped_coro(), name=name, context=context)
    
    # Apply the patch
    asyncio.create_task = _patched_create_task
    logger.info("Patched asyncio.create_task for better error handling")

if __name__ == "__main__":
    # Test the patch when run directly
    logging.basicConfig(level=logging.INFO)
    applied = apply_patches()
    print(f"Asyncio patches applied: {applied}")
