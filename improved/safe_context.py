#!/usr/bin/env python3

"""
SafeContext - A wrapper for MCP context that handles different context interfaces
and provides fallback for missing methods.
"""

import logging
from typing import Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class SafeContext:
    """
    Wrapper for MCP context that handles different context interfaces
    and provides fallback for missing methods.
    
    This class provides compatibility with different versions of the MCP SDK
    and gracefully handles missing methods.
    """
    def __init__(self, ctx: Any):
        """Initialize with an MCP context object"""
        self.ctx = ctx
    
    async def info(self, message: str) -> None:
        """Send info message to the client"""
        if self.ctx is None:
            logger.info(message)
            return
        
        if hasattr(self.ctx, 'info'):
            await self.ctx.info(message)
        elif hasattr(self.ctx, 'send_info'):
            await self.ctx.send_info(message)
        else:
            logger.info(message)
    
    async def error(self, message: str) -> None:
        """Send error message to the client"""
        if self.ctx is None:
            logger.error(message)
            return
        
        if hasattr(self.ctx, 'error'):
            await self.ctx.error(message)
        elif hasattr(self.ctx, 'send_error'):
            await self.ctx.send_error(message)
        else:
            logger.error(message)
    
    async def warning(self, message: str) -> None:
        """Send warning message to the client"""
        if self.ctx is None:
            logger.warning(message)
            return
        
        if hasattr(self.ctx, 'warning'):
            await self.ctx.warning(message)
        elif hasattr(self.ctx, 'send_warning'):
            await self.ctx.send_warning(message)
        else:
            logger.warning(message)
    
    async def progress(self, message: str, percentage: Union[int, float]) -> None:
        """Send progress update to the client with percentage and message"""
        if self.ctx is None:
            logger.info(f"Progress {percentage}%: {message}")
            return
        
        if hasattr(self.ctx, 'progress'):
            await self.ctx.progress(message, percentage)
        elif hasattr(self.ctx, 'report_progress'):
            # MCP 1.x uses report_progress(current, total)
            # MCP 2.x uses report_progress(current, total, message)
            # We need to check the signature and adapt accordingly
            import inspect
            sig = inspect.signature(self.ctx.report_progress)
            param_count = len(sig.parameters)
            
            if param_count == 2:
                # MCP 1.x: report_progress(current, total)
                await self.ctx.report_progress(int(percentage), 100)
            elif param_count == 3:
                # MCP 2.x: report_progress(current, total, message)
                await self.ctx.report_progress(int(percentage), 100, message)
            else:
                logger.warning(f"Unexpected report_progress signature with {param_count} parameters")
                # Fallback to the most common signature
                try:
                    await self.ctx.report_progress(int(percentage), 100)
                except Exception as e:
                    logger.error(f"Error reporting progress: {e}")
        else:
            logger.info(f"Progress {percentage}%: {message}")
    
    async def report_progress(self, current: Union[int, float], total: Union[int, float], message: str = "") -> None:
        """Report progress with current/total values and optional message"""
        percentage = int((current / total) * 100) if total > 0 else 0
        await self.progress(message, percentage)
