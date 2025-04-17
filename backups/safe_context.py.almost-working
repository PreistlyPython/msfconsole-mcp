#!/usr/bin/env python3

"""
Safe Context - A wrapper for MCP context objects for the MSFconsole MCP
This module ensures proper compatibility with the MCP SDK, handling missing attributes gracefully
"""

import logging
from typing import Optional, Any, Union

class SafeContext:
    """Safe context wrapper that handles missing attributes gracefully."""
    
    def __init__(self, ctx=None):
        self.ctx = ctx
        self.logger = logging.getLogger("SafeContext")
    
    async def report_progress(self, current: Union[int, float], total: Optional[Union[int, float]] = None, message: Optional[str] = None) -> bool:
        """
        Safely report progress, with fallbacks for different context APIs.
        
        Args:
            current: Current progress value
            total: Total progress value (default: None)
            message: Progress message to display
            
        Returns:
            bool: True if progress was reported, False otherwise
        """
        if message:
            self.logger.info(f"Progress: {message}")
            
        if self.ctx is None:
            return True
            
        try:
            # Try different progress reporting methods based on available attributes
            if hasattr(self.ctx, 'report_progress'):
                # New API style
                if total is not None:
                    await self.ctx.report_progress(current, total)
                else:
                    await self.ctx.report_progress(current)
                return True
            elif hasattr(self.ctx, 'progress'):
                # Old API style (deprecated)
                if message:
                    await self.ctx.progress(message, current)
                else:
                    await self.ctx.progress(f"Progress: {current}%", current)
                return True
            else:
                # No progress method available, use info logging as fallback
                if message:
                    await self.info(f"Progress ({current}%): {message}")
                else:
                    await self.info(f"Progress: {current}%")
                return True
        except Exception as e:
            self.logger.warning(f"Error reporting progress: {e}")
            # Fall back to local logging on exception
            self.logger.info(f"Progress: {current}% - {message if message else ''}")
            return False
    
    async def log(self, level: str, message: str, **extra) -> None:
        """
        Log a message using the appropriate context method or fallback to local logging.
        
        Args:
            level: Log level (info, error, warning, debug)
            message: Log message
            **extra: Additional keyword arguments to pass to logging
        """
        # Always log locally first
        if level == "info":
            self.logger.info(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "debug":
            self.logger.debug(message)
        
        if self.ctx is None:
            return
            
        try:
            # Try to use the appropriate context method
            if level == "info" and hasattr(self.ctx, "info"):
                await self.ctx.info(message, **extra)
            elif level == "error" and hasattr(self.ctx, "error"):
                await self.ctx.error(message, **extra)
            elif level == "warning" and hasattr(self.ctx, "warning"):
                await self.ctx.warning(message, **extra)
            elif level == "debug" and hasattr(self.ctx, "debug"):
                await self.ctx.debug(message, **extra)
            elif hasattr(self.ctx, "log"):
                # Fallback to generic log method
                await self.ctx.log(level, message, **extra)
        except Exception as e:
            self.logger.warning(f"Error when using context.{level}(): {e}")
    
    async def info(self, message: str, **extra) -> None:
        """Log an info message."""
        await self.log("info", message, **extra)
    
    async def error(self, message: str, **extra) -> None:
        """Log an error message."""
        await self.log("error", message, **extra)
    
    async def warning(self, message: str, **extra) -> None:
        """Log a warning message."""
        await self.log("warning", message, **extra)
    
    async def debug(self, message: str, **extra) -> None:
        """Log a debug message."""
        await self.log("debug", message, **extra)
