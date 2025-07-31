#!/usr/bin/env python3

"""
Metasploit Dual-Mode Operation Handler
--------------------------------------
Handles both RPC and Resource Script modes with automatic fallback.
"""

import asyncio
import logging
import tempfile
import os
import shutil
import subprocess
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from msf_rpc_manager import MSFRPCManager, RPCConfig

logger = logging.getLogger(__name__)

class OperationMode(Enum):
    RPC = "rpc"
    RESOURCE_SCRIPT = "resource_script"
    AUTO = "auto"

@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str = ""
    mode_used: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = None

class MSFDualModeHandler:
    """
    Handles dual-mode operation for Metasploit integration.
    Automatically switches between RPC and Resource Script modes based on availability.
    """
    
    def __init__(self, rpc_config: RPCConfig = None):
        self.rpc_manager = MSFRPCManager(rpc_config)
        self.preferred_mode = OperationMode.RPC
        self.current_mode = OperationMode.AUTO
        self.msfconsole_path = self._find_msfconsole()
        self.msfvenom_path = self._find_msfvenom()
        self.default_workspace = "default"
        self.active_consoles = {}  # Track active console sessions
        
    async def initialize(self) -> bool:
        """
        Initialize the dual-mode handler.
        
        Returns:
            bool: True if initialized successfully
        """
        logger.info("Initializing MSF Dual-Mode Handler...")
        
        # Try to start RPC mode first
        try:
            if await self.rpc_manager.start():
                self.current_mode = OperationMode.RPC
                logger.info("RPC mode initialized successfully")
                return True
        except Exception as e:
            logger.warning(f"RPC mode initialization failed: {e}")
        
        # Fallback to resource script mode
        if self.msfconsole_path:
            self.current_mode = OperationMode.RESOURCE_SCRIPT
            logger.info("Falling back to Resource Script mode")
            return True
        else:
            logger.error("Neither RPC nor Resource Script mode available")
            return False
    
    async def shutdown(self):
        """Shutdown the dual-mode handler."""
        logger.info("Shutting down MSF Dual-Mode Handler...")
        
        # Close any active consoles
        for console_id in list(self.active_consoles.keys()):
            await self._cleanup_console(console_id)
        
        # Stop RPC manager
        await self.rpc_manager.stop()
        
        logger.info("MSF Dual-Mode Handler shutdown complete")
    
    async def execute_command(self, command: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """
        Execute a command using the best available mode.
        
        Args:
            command: Metasploit command to execute
            context: Additional context for execution
            
        Returns:
            ExecutionResult containing the results
        """
        import time
        start_time = time.time()
        
        context = context or {}
        
        # Determine the best mode for this command
        optimal_mode = self._determine_optimal_mode(command, context)
        
        try:
            if optimal_mode == OperationMode.RPC and self.rpc_manager.is_connected:
                result = await self._execute_rpc_command(command, context)
                result.mode_used = "rpc"
            else:
                result = await self._execute_resource_script_command(command, context)
                result.mode_used = "resource_script"
            
            result.execution_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            
            # Try fallback mode if primary failed
            if optimal_mode == OperationMode.RPC:
                logger.info("RPC execution failed, trying resource script fallback")
                try:
                    result = await self._execute_resource_script_command(command, context)
                    result.mode_used = "resource_script_fallback"
                    result.execution_time = time.time() - start_time
                    return result
                except Exception as fallback_error:
                    logger.error(f"Fallback execution also failed: {fallback_error}")
            
            # Return error result
            return ExecutionResult(
                success=False,
                output="",
                error=str(e),
                mode_used=optimal_mode.value,
                execution_time=time.time() - start_time
            )
    
    async def execute_batch_commands(self, commands: List[str], context: Dict[str, Any] = None) -> List[ExecutionResult]:
        """
        Execute multiple commands in batch.
        
        Args:
            commands: List of commands to execute
            context: Execution context
            
        Returns:
            List of ExecutionResults
        """
        context = context or {}
        results = []
        
        # For batch operations, resource scripts are often more efficient
        if len(commands) > 3 and self.msfconsole_path:
            logger.info(f"Executing {len(commands)} commands as batch resource script")
            batch_result = await self._execute_batch_resource_script(commands, context)
            results.append(batch_result)
        else:
            # Execute individually
            for command in commands:
                result = await self.execute_command(command, context)
                results.append(result)
        
        return results
    
    async def get_persistent_console(self, console_id: str = None) -> str:
        """
        Get or create a persistent console session.
        
        Args:
            console_id: Optional existing console ID
            
        Returns:
            Console ID for subsequent operations
        """
        if console_id and console_id in self.active_consoles:
            return console_id
        
        if self.rpc_manager.is_connected:
            # Create RPC console
            response = await self.rpc_manager.call("console.create")
            new_console_id = response.get("id")
            
            if new_console_id:
                self.active_consoles[new_console_id] = {
                    "type": "rpc",
                    "created_at": asyncio.get_event_loop().time()
                }
                logger.info(f"Created RPC console: {new_console_id}")
                return new_console_id
        
        # Fallback: generate unique ID for resource script mode
        import uuid
        console_id = f"rs_{uuid.uuid4().hex[:8]}"
        self.active_consoles[console_id] = {
            "type": "resource_script",
            "created_at": asyncio.get_event_loop().time()
        }
        logger.info(f"Created resource script console: {console_id}")
        return console_id
    
    async def execute_in_console(self, console_id: str, command: str) -> ExecutionResult:
        """
        Execute a command in a specific console.
        
        Args:
            console_id: Console ID
            command: Command to execute
            
        Returns:
            ExecutionResult
        """
        if console_id not in self.active_consoles:
            raise ValueError(f"Console {console_id} not found")
        
        console_info = self.active_consoles[console_id]
        
        if console_info["type"] == "rpc" and self.rpc_manager.is_connected:
            return await self._execute_rpc_console_command(console_id, command)
        else:
            return await self._execute_resource_script_command(command, {"console_id": console_id})
    
    def _determine_optimal_mode(self, command: str, context: Dict[str, Any]) -> OperationMode:
        """Determine the optimal execution mode for a command."""
        
        # Interactive commands work better with RPC
        interactive_commands = ['sessions', 'interact', 'shell', 'meterpreter']
        if any(cmd in command.lower() for cmd in interactive_commands):
            if self.rpc_manager.is_connected:
                return OperationMode.RPC
        
        # Batch operations work better with resource scripts
        if context.get('batch_mode', False):
            return OperationMode.RESOURCE_SCRIPT
        
        # Database operations work well with either mode
        db_commands = ['hosts', 'services', 'vulns', 'db_status']
        if any(cmd in command.lower() for cmd in db_commands):
            return OperationMode.RPC if self.rpc_manager.is_connected else OperationMode.RESOURCE_SCRIPT
        
        # Default to RPC if available, otherwise resource script
        return OperationMode.RPC if self.rpc_manager.is_connected else OperationMode.RESOURCE_SCRIPT
    
    async def _execute_rpc_command(self, command: str, context: Dict[str, Any]) -> ExecutionResult:
        """Execute command using RPC mode."""
        try:
            # Use console API for command execution
            console_id = context.get('console_id')
            
            if not console_id:
                # Create temporary console
                console_response = await self.rpc_manager.call("console.create")
                console_id = console_response.get("id")
                temp_console = True
            else:
                temp_console = False
            
            # Execute command
            result = await self.rpc_manager.execute_console_command(command, console_id)
            
            # Clean up temporary console
            if temp_console:
                try:
                    await self.rpc_manager.call("console.destroy", [console_id])
                except Exception as e:
                    logger.warning(f"Failed to destroy temporary console: {e}")
            
            return ExecutionResult(
                success=True,
                output=result.get("output", ""),
                metadata={
                    "console_id": console_id,
                    "busy": result.get("busy", False)
                }
            )
            
        except Exception as e:
            logger.error(f"RPC command execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def _execute_rpc_console_command(self, console_id: str, command: str) -> ExecutionResult:
        """Execute command in a specific RPC console."""
        try:
            result = await self.rpc_manager.execute_console_command(command, console_id)
            
            return ExecutionResult(
                success=True,
                output=result.get("output", ""),
                metadata={
                    "console_id": console_id,
                    "busy": result.get("busy", False)
                }
            )
            
        except Exception as e:
            logger.error(f"RPC console command execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def _execute_resource_script_command(self, command: str, context: Dict[str, Any]) -> ExecutionResult:
        """Execute command using resource script mode."""
        try:
            # Create temporary resource script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as script_file:
                # Add database initialization for commands that need it
                db_commands = ['hosts', 'services', 'vulns', 'creds', 'loot', 'notes', 'search']
                needs_db = any(db_cmd in command.lower() for db_cmd in db_commands)
                if needs_db:
                    script_file.write("db_status\n")  # Check database connection
                
                # Add workspace setup if specified
                workspace = context.get('workspace', self.default_workspace)
                if workspace != 'default':
                    script_file.write(f"workspace {workspace}\n")
                
                # Add the command
                script_file.write(f"{command}\n")
                script_file.write("exit\n")
                script_path = script_file.name
            
            # Execute msfconsole with the resource script
            cmd = [self.msfconsole_path, "-q", "-r", script_path]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=context.get('timeout', 300)  # Use 5 minutes default
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                raise TimeoutError("Command execution timed out")
            
            # Clean up
            try:
                os.unlink(script_path)
            except Exception as e:
                logger.warning(f"Failed to clean up script file: {e}")
            
            stdout_text = stdout.decode('utf-8', errors='replace')
            stderr_text = stderr.decode('utf-8', errors='replace')
            
            return ExecutionResult(
                success=process.returncode == 0,
                output=stdout_text,
                error=stderr_text,
                metadata={
                    "return_code": process.returncode,
                    "script_path": script_path
                }
            )
            
        except Exception as e:
            logger.error(f"Resource script execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def _execute_batch_resource_script(self, commands: List[str], context: Dict[str, Any]) -> ExecutionResult:
        """Execute multiple commands as a single resource script."""
        try:
            # Create batch resource script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as script_file:
                # Add workspace setup
                workspace = context.get('workspace', self.default_workspace)
                if workspace != 'default':
                    script_file.write(f"workspace {workspace}\n")
                
                # Add all commands
                for command in commands:
                    script_file.write(f"{command}\n")
                
                script_file.write("exit\n")
                script_path = script_file.name
            
            # Execute the batch script
            result = await self._execute_resource_script_command("", {
                **context,
                'script_path': script_path
            })
            
            result.metadata = result.metadata or {}
            result.metadata['batch_size'] = len(commands)
            result.metadata['commands'] = commands
            
            return result
            
        except Exception as e:
            logger.error(f"Batch resource script execution failed: {e}")
            return ExecutionResult(
                success=False,
                output="",
                error=str(e)
            )
    
    async def _cleanup_console(self, console_id: str):
        """Clean up a console session."""
        if console_id not in self.active_consoles:
            return
        
        console_info = self.active_consoles[console_id]
        
        if console_info["type"] == "rpc" and self.rpc_manager.is_connected:
            try:
                await self.rpc_manager.call("console.destroy", [console_id])
                logger.info(f"Destroyed RPC console: {console_id}")
            except Exception as e:
                logger.warning(f"Failed to destroy RPC console {console_id}: {e}")
        
        del self.active_consoles[console_id]
    
    def _find_msfconsole(self) -> Optional[str]:
        """Find msfconsole executable."""
        paths = [
            "/usr/bin/msfconsole",
            "/opt/metasploit-framework/bin/msfconsole",
        ]
        
        for path in paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try to find in PATH
        return shutil.which("msfconsole")
    
    def _find_msfvenom(self) -> Optional[str]:
        """Find msfvenom executable."""
        paths = [
            "/usr/bin/msfvenom",
            "/opt/metasploit-framework/bin/msfvenom",
        ]
        
        for path in paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Try to find in PATH
        return shutil.which("msfvenom")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the dual-mode handler."""
        return {
            "current_mode": self.current_mode.value,
            "preferred_mode": self.preferred_mode.value,
            "rpc_connected": self.rpc_manager.is_connected,
            "rpc_status": self.rpc_manager.get_status(),
            "msfconsole_available": bool(self.msfconsole_path),
            "msfvenom_available": bool(self.msfvenom_path),
            "active_consoles": len(self.active_consoles),
            "console_ids": list(self.active_consoles.keys())
        }