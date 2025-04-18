#!/usr/bin/env python3

"""
Metasploit Process Manager
--------------------------
This module handles the interaction with the Metasploit process, including
command execution, output parsing, and error handling.
"""

import os
import re
import time
import asyncio
import logging
from typing import Optional, List, Tuple, Dict, Any, Union

# Get logger
logger = logging.getLogger("msfconsole_mcp")

class MetasploitProcessError(Exception):
    """Custom exception for Metasploit process errors."""
    pass

class CommandTimeoutError(MetasploitProcessError):
    """Exception raised when a command times out."""
    pass

class ProcessNotRunningError(MetasploitProcessError):
    """Exception raised when trying to interact with a process that isn't running."""
    pass

class OutputParsingError(MetasploitProcessError):
    """Exception raised when output cannot be parsed correctly."""
    pass

class MetasploitProcess:
    """
    Manages interaction with Metasploit processes and ensures
    proper handling of stdin/stdout/stderr with enhanced error handling.
    """
    def __init__(self, executable_path: str = "/usr/bin/msfconsole"):
        """
        Initialize the Metasploit process manager.
        
        Args:
            executable_path: Path to the msfconsole executable
        """
        self.executable_path = executable_path
        self.process = None
        self.command_queue = asyncio.Queue()
        self.result_queue = asyncio.Queue()
        self.running = False
        self.command_timeout = 30  # Default timeout in seconds
        
        # Track active commands for debugging
        self.active_commands = {}
        
        # Track the current command marker
        self.current_marker = None
        
        # MSFCONSOLE prompt detector
        self.stdout_buffer = ""
        self.stderr_buffer = ""
        self.prompt_detected = asyncio.Event()

    async def start(self) -> bool:
        """
        Start the Metasploit console process with enhanced error handling.
        
        Returns:
            True if started successfully
        
        Raises:
            FileNotFoundError: If msfconsole executable is not found
            RuntimeError: If process fails to start
        """
        logger.info("Starting Metasploit console process...")
        
        # Check if msfconsole exists and is executable
        if not os.path.isfile(self.executable_path) or not os.access(self.executable_path, os.X_OK):
            error_msg = f"Metasploit console not found at {self.executable_path} or not executable"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        try:
            # Start msfconsole with -q (quiet) and -n (non-interactive) flags
            self.process = await asyncio.create_subprocess_exec(
                self.executable_path, 
                "-q",  # Quiet mode to reduce banner output
                "-n",  # Non-interactive mode
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            if not self.process or self.process.returncode is not None:
                error_msg = "Failed to start Metasploit process"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            
            logger.info(f"Metasploit process started with PID: {self.process.pid}")
            self.running = True
            
            # Start the management tasks
            asyncio.create_task(self._process_stdout())
            asyncio.create_task(self._process_stderr())
            asyncio.create_task(self._command_processor())
            
            # Wait for prompt to ensure process is ready
            try:
                await asyncio.wait_for(self.prompt_detected.wait(), 10)
                logger.info("Metasploit console started successfully and ready for commands")
                return True
            except asyncio.TimeoutError:
                logger.warning("Metasploit console started but prompt not detected. Continuing anyway.")
                return True
                
        except Exception as e:
            logger.error(f"Failed to start Metasploit console: {str(e)}")
            raise

    async def execute_command(self, command: str, timeout: int = None) -> str:
        """
        Execute a command in the Metasploit console with enhanced error handling.
        
        Args:
            command: The command to execute
            timeout: Optional timeout in seconds (defaults to self.command_timeout)
        
        Returns:
            The command output as a string
        
        Raises:
            ProcessNotRunningError: If the Metasploit process is not running
            CommandTimeoutError: If the command execution times out
            OutputParsingError: If the output cannot be parsed correctly
        """
        if not self.running or not self.process or self.process.returncode is not None:
            error_msg = "Metasploit console is not running"
            logger.error(error_msg)
            raise ProcessNotRunningError(error_msg)
        
        # Use specified timeout or default
        timeout = timeout or self.command_timeout
        
        # Generate a unique marker for this command for debugging
        cmd_marker = str(int(time.time()))
        self.current_marker = cmd_marker
        logger.debug(f"[{cmd_marker}] Executing command: {command}")
        
        # Track the command
        self.active_commands[cmd_marker] = {
            'command': command,
            'started_at': time.time(),
            'timeout': timeout
        }
        
        try:
            # Queue the command
            await self.command_queue.put(command)
            
            # Wait for result with timeout
            start_time = time.time()
            while True:
                try:
                    # Check if we have output to process
                    if self.result_queue.empty():
                        # Check for timeout
                        if time.time() - start_time > timeout:
                            logger.error(f"[{cmd_marker}] Command timed out after {timeout} seconds: {command}")
                            del self.active_commands[cmd_marker]
                            self.current_marker = None
                            raise CommandTimeoutError(f"Command execution timed out: {command}")
                        
                        # Wait a bit before checking again
                        await asyncio.sleep(0.1)
                        continue
                    
                    # Got a result
                    result = await self.result_queue.get()
                    logger.debug(f"[{cmd_marker}] Command completed successfully")
                    del self.active_commands[cmd_marker]
                    self.current_marker = None
                    return result
                    
                except asyncio.CancelledError:
                    logger.warning(f"[{cmd_marker}] Command execution cancelled")
                    del self.active_commands[cmd_marker]
                    self.current_marker = None
                    raise
                    
        except Exception as e:
            if not isinstance(e, (CommandTimeoutError, asyncio.CancelledError)):
                logger.error(f"[{cmd_marker}] Error executing command: {e}")
            if cmd_marker in self.active_commands:
                del self.active_commands[cmd_marker]
            self.current_marker = None
            raise

    async def stop(self) -> None:
        """
        Stop the Metasploit console process with graceful shutdown.
        """
        if self.process and self.process.returncode is None:
            logger.info("Stopping Metasploit console process...")
            try:
                # Try to exit gracefully
                await self.execute_command("exit", timeout=5)
            except Exception as e:
                logger.warning(f"Error during graceful shutdown: {e}")
            
            # Terminate if still running
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), 5)
                logger.info("Metasploit process terminated")
            except (asyncio.TimeoutError, ProcessLookupError) as e:
                logger.warning(f"Force killing Metasploit console process: {e}")
                try:
                    self.process.kill()
                    await self.process.wait()
                except ProcessLookupError:
                    # Process already gone
                    pass
                
        self.running = False
        logger.info("Metasploit console stopped")

    async def _process_stdout(self) -> None:
        """
        Process stdout from the Metasploit console with enhanced error detection.
        """
        prompt_pattern = r"\s*msf\w*\s*>\s*$"
        
        while self.running and self.process and not self.process.stdout.at_eof():
            try:
                # Read a chunk of data
                data = await self.process.stdout.read(1024)
                if not data:
                    logger.warning("No data received from stdout, stream may have closed")
                    break
                
                # Decode and add to buffer
                chunk = data.decode("utf-8", errors="replace")
                self.stdout_buffer += chunk
                
                # Check for prompt in the buffer
                if re.search(prompt_pattern, self.stdout_buffer, re.MULTILINE):
                    # Prompt detected - set the event
                    if not self.prompt_detected.is_set():
                        logger.debug("Initial prompt detected")
                        self.prompt_detected.set()
                    
                    # Debug log the raw output if we have an active command
                    if self.current_marker:
                        logger.debug(f"[{self.current_marker}] Raw stdout: {chunk}")
                        logger.debug(f"[{self.current_marker}] Command completed, detected prompt")
                        result = self.stdout_buffer.strip()
                        self.stdout_buffer = ""
                        
                        # Put result in queue
                        await self.result_queue.put(result)
                        self.current_marker = None
                    else:
                        # No current command, just clear the buffer
                        self.stdout_buffer = ""
                
                # Check for error or success patterns for better logging
                if self.current_marker:
                    error_match = re.search(r"\s*\[-\]\s*(.*?)$", self.stdout_buffer, re.MULTILINE)
                    if error_match:
                        error_msg = error_match.group(1)
                        logger.warning(f"[{self.current_marker}] Command error detected: {error_msg}")
                    
                    success_match = re.search(r"\s*\[\+\]\s*(.*?)$", self.stdout_buffer, re.MULTILINE)
                    if success_match:
                        success_msg = success_match.group(1)
                        logger.debug(f"[{self.current_marker}] Command success detected: {success_msg}")
                
            except Exception as e:
                logger.error(f"Error processing stdout: {e}")
                # Don't lose the buffer on error
                if self.current_marker and self.stdout_buffer:
                    logger.debug(f"[{self.current_marker}] Saving partial output due to error: {self.stdout_buffer}")
                    await self.result_queue.put(f"ERROR processing output: {e}\n\nPartial output:\n{self.stdout_buffer}")
                    self.current_marker = None
                    self.stdout_buffer = ""
                await asyncio.sleep(0.1)  # Avoid tight loop on errors
        
        logger.warning("Stdout processing stopped")
        # Clear any pending commands
        if self.current_marker:
            logger.warning(f"[{self.current_marker}] Process stopped while command was active")
            await self.result_queue.put(f"ERROR: Process stopped while command was active\n\nPartial output:\n{self.stdout_buffer}")
            self.current_marker = None
            self.stdout_buffer = ""

    async def _process_stderr(self) -> None:
        """
        Process stderr from the Metasploit console with error categorization.
        """
        while self.running and self.process and not self.process.stderr.at_eof():
            try:
                data = await self.process.stderr.read(1024)
                if not data:
                    logger.warning("No data received from stderr, stream may have closed")
                    break
                
                # Log stderr output
                stderr_text = data.decode("utf-8", errors="replace").strip()
                self.stderr_buffer += stderr_text
                
                if stderr_text:
                    # Try to categorize the error
                    if "Error:" in stderr_text:
                        logger.error(f"Metasploit stderr ERROR: {stderr_text}")
                    elif "Warning:" in stderr_text:
                        logger.warning(f"Metasploit stderr WARNING: {stderr_text}")
                    else:
                        logger.info(f"Metasploit stderr: {stderr_text}")
                    
                    # Associate with current command if there is one
                    if self.current_marker:
                        logger.debug(f"[{self.current_marker}] Associated stderr: {stderr_text}")
                
            except Exception as e:
                logger.error(f"Error processing stderr: {e}")
                await asyncio.sleep(0.1)  # Avoid tight loop on errors
        
        logger.warning("Stderr processing stopped")

    async def _command_processor(self) -> None:
        """
        Process commands from the queue and send to Metasploit console.
        """
        while self.running:
            try:
                # Get command from queue
                command = await self.command_queue.get()
                logger.debug(f"Processing command from queue: {command}")
                
                # Send command to process
                if self.process and self.process.stdin and not self.process.stdin.is_closing():
                    cmd_bytes = f"{command}\n".encode("utf-8")
                    self.process.stdin.write(cmd_bytes)
                    await self.process.stdin.drain()
                    logger.debug(f"Command sent to Metasploit")
                else:
                    error_msg = "Cannot send command: stdin not available"
                    logger.error(error_msg)
                    await self.result_queue.put(f"ERROR: {error_msg}")
                
                # Mark command as done
                self.command_queue.task_done()
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                await self.result_queue.put(f"ERROR: Error sending command: {e}")
                await asyncio.sleep(0.1)  # Prevent tight loop on errors
