#!/usr/bin/env python3

"""
SafeContext - A robust wrapper for MCP context that handles different API versions.

This implementation supports cross-version compatibility and gracefully
handles different MCP SDK signatures for progress reporting.
"""

import logging
import inspect
from typing import Any, Dict, List, Optional, Union, Tuple, Callable

# Configure logging
logger = logging.getLogger(__name__)

class SafeContext:
    """
    A wrapper for MCP Context that handles different API versions and signatures.
    
    This class provides compatibility with different versions of the MCP SDK
    and gracefully handles missing methods or signature changes. It uses
    Python's introspection capabilities to adapt to different SDK versions.
    
    Key features:
    - Automatic signature detection for methods
    - Fallback mechanisms for missing methods
    - Structured logging for diagnostics
    - Transparent version compatibility
    """
    
    def __init__(self, ctx: Any):
        """
        Initialize with an MCP context object.
        
        Args:
            ctx: An MCP Context object from any SDK version
        """
        self.ctx = ctx
        self._inspect_context()
    
    def _inspect_context(self):
        """Inspect the context object to determine available methods and signatures"""
        self._context_capabilities = {
            'has_info': hasattr(self.ctx, 'info'),
            'has_error': hasattr(self.ctx, 'error'),
            'has_warning': hasattr(self.ctx, 'warning'),
            'has_progress': hasattr(self.ctx, 'progress'),
            'has_report_progress': hasattr(self.ctx, 'report_progress'),
        }
        
        # Inspect report_progress signature if available
        if self._context_capabilities['has_report_progress']:
            try:
                self._report_progress_sig = inspect.signature(self.ctx.report_progress)
                self._report_progress_params = len(self._report_progress_sig.parameters)
                logger.info(f"Detected report_progress with {self._report_progress_params} parameters")
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not inspect report_progress signature: {e}")
                self._report_progress_params = 2  # Default to the most basic signature
        else:
            self._report_progress_params = 0
            
    async def info(self, message: str) -> None:
        """
        Send info message to the client.
        
        Args:
            message: Informational message to log
        """
        if self.ctx is None:
            logger.info(message)
            return
        
        if hasattr(self.ctx, 'info'):
            try:
                await self.ctx.info(message)
            except Exception as e:
                logger.error(f"Error calling ctx.info: {e}")
                logger.info(message)
        elif hasattr(self.ctx, 'send_info'):
            try:
                await self.ctx.send_info(message)
            except Exception as e:
                logger.error(f"Error calling ctx.send_info: {e}")
                logger.info(message)
        else:
            logger.info(message)
    
    async def error(self, message: str) -> None:
        """
        Send error message to the client.
        
        Args:
            message: Error message to log
        """
        if self.ctx is None:
            logger.error(message)
            return
        
        if hasattr(self.ctx, 'error'):
            try:
                await self.ctx.error(message)
            except Exception as e:
                logger.error(f"Error calling ctx.error: {e}")
                logger.error(message)
        elif hasattr(self.ctx, 'send_error'):
            try:
                await self.ctx.send_error(message)
            except Exception as e:
                logger.error(f"Error calling ctx.send_error: {e}")
                logger.error(message)
        else:
            logger.error(message)
    
    async def warning(self, message: str) -> None:
        """
        Send warning message to the client.
        
        Args:
            message: Warning message to log
        """
        if self.ctx is None:
            logger.warning(message)
            return
        
        if hasattr(self.ctx, 'warning'):
            try:
                await self.ctx.warning(message)
            except Exception as e:
                logger.error(f"Error calling ctx.warning: {e}")
                logger.warning(message)
        elif hasattr(self.ctx, 'send_warning'):
            try:
                await self.ctx.send_warning(message)
            except Exception as e:
                logger.error(f"Error calling ctx.send_warning: {e}")
                logger.warning(message)
        else:
            logger.warning(message)
    
    async def progress(self, message: str, percentage: Union[int, float]) -> None:
        """
        Send progress update to the client with percentage and message.
        
        This method adapts to various MCP Context API styles for reporting progress.
        
        Args:
            message: Description of the current progress state
            percentage: Progress value (0-100)
        """
        if self.ctx is None:
            logger.info(f"Progress {percentage}%: {message}")
            return
        
        # Handle different progress reporting styles
        try:
            if hasattr(self.ctx, 'progress'):
                await self.ctx.progress(message, percentage)
            elif hasattr(self.ctx, 'report_progress'):
                await self._call_report_progress(percentage, 100, message)
            else:
                logger.info(f"Progress {percentage}%: {message}")
        except Exception as e:
            logger.error(f"Error reporting progress: {e}")
            logger.info(f"Progress {percentage}%: {message}")
    
    async def _call_report_progress(self, current: Union[int, float], 
                                   total: Union[int, float], 
                                   message: Optional[str] = None) -> None:
        """
        Call the appropriate report_progress method based on its signature.
        
        This internal method handles the complexity of different MCP SDK versions.
        
        Args:
            current: Current progress value
            total: Total progress value (for calculating percentage)
            message: Optional progress message
        """
        # Ensure we have integers for progress values
        current_int = int(current)
        total_int = int(total)
        
        try:
            # Call the appropriate signature based on SDK version
            if self._report_progress_params == 2:
                # MCP 1.x: report_progress(current, total)
                await self.ctx.report_progress(current_int, total_int)
            elif self._report_progress_params == 3:
                # MCP 2.x: report_progress(current, total, message)
                if message is not None:
                    await self.ctx.report_progress(current_int, total_int, message)
                else:
                    await self.ctx.report_progress(current_int, total_int, "")
            else:
                logger.warning(f"Unexpected report_progress signature with {self._report_progress_params} parameters")
                # Try the basic signature as fallback
                await self.ctx.report_progress(current_int, total_int)
        except Exception as e:
            logger.error(f"Error calling report_progress: {e}")
    
    async def report_progress(self, current: Union[int, float], 
                             total: Union[int, float], 
                             message: str = "") -> None:
        """
        Report progress with current/total values and optional message.
        
        This is the primary method for reporting progress from client code.
        
        Args:
            current: Current progress value
            total: Total progress value (for calculating percentage)
            message: Optional progress message
        """
        # Calculate percentage
        percentage = int((current / total) * 100) if total > 0 else 0
        
        # Normalize percentage to 0-100 range
        percentage = max(0, min(100, percentage))
        
        if hasattr(self.ctx, 'report_progress'):
            await self._call_report_progress(current, total, message)
        else:
            # If there's no direct report_progress, use our progress method
            await self.progress(message, percentage)
