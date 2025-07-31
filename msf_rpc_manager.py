#!/usr/bin/env python3

"""
Metasploit RPC Connection Manager
---------------------------------
Handles RPC connections to msfrpcd with automatic reconnection,
connection pooling, and health checking.
"""

import asyncio
import aiohttp
import json
import logging
import time
import subprocess
import os
import signal
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"

@dataclass
class RPCConfig:
    host: str = "127.0.0.1"
    port: int = 55552
    username: str = "msf"
    password: str = "msf123"
    ssl: bool = False
    timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 5

class MSFRPCManager:
    """
    Manages connections to Metasploit RPC server with automatic reconnection,
    health checking, and connection pooling.
    """
    
    def __init__(self, config: RPCConfig = None):
        self.config = config or RPCConfig()
        self.state = ConnectionState.DISCONNECTED
        self.session = None
        self.auth_token = None
        self.msfrpcd_process = None
        self.connection_pool = []
        self.health_check_task = None
        self.reconnect_task = None
        self.request_id = 0
        self.last_health_check = 0
        self.connection_failures = 0
        
        # Create session with proper SSL handling
        self._setup_session()
    
    def _setup_session(self):
        """Setup aiohttp session with SSL configuration."""
        connector = aiohttp.TCPConnector(
            ssl=False if not self.config.ssl else None,
            limit=10,  # Connection pool limit
            limit_per_host=5,
            ttl_dns_cache=300,
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'Content-Type': 'application/json'}
        )
    
    async def start(self) -> bool:
        """
        Start the RPC manager, including msfrpcd if needed.
        
        Returns:
            bool: True if successfully started, False otherwise
        """
        logger.info("Starting MSF RPC Manager...")
        
        try:
            # Check if msfrpcd is already running
            if await self._check_rpc_server():
                logger.info("Found existing msfrpcd server")
            else:
                # Start msfrpcd
                if not await self._start_msfrpcd():
                    logger.error("Failed to start msfrpcd")
                    return False
            
            # Connect to the server
            if await self.connect():
                # Start health checking
                self.health_check_task = asyncio.create_task(self._health_check_loop())
                logger.info("MSF RPC Manager started successfully")
                return True
            else:
                logger.error("Failed to connect to RPC server")
                return False
                
        except Exception as e:
            logger.error(f"Error starting RPC manager: {e}")
            return False
    
    async def stop(self):
        """Stop the RPC manager and cleanup resources."""
        logger.info("Stopping MSF RPC Manager...")
        
        # Cancel health checking
        if self.health_check_task:
            self.health_check_task.cancel()
            try:
                await self.health_check_task
            except asyncio.CancelledError:
                pass
        
        # Cancel reconnection task
        if self.reconnect_task:
            self.reconnect_task.cancel()
            try:
                await self.reconnect_task
            except asyncio.CancelledError:
                pass
        
        # Close session
        if self.session:
            await self.session.close()
        
        # Stop msfrpcd if we started it
        if self.msfrpcd_process:
            await self._stop_msfrpcd()
        
        self.state = ConnectionState.DISCONNECTED
        logger.info("MSF RPC Manager stopped")
    
    async def connect(self) -> bool:
        """
        Connect to the RPC server and authenticate.
        
        Returns:
            bool: True if connected successfully, False otherwise
        """
        if self.state == ConnectionState.CONNECTING:
            return False
        
        self.state = ConnectionState.CONNECTING
        logger.info(f"Connecting to MSF RPC at {self.config.host}:{self.config.port}")
        
        try:
            # Authenticate
            auth_response = await self._rpc_call("auth.login", [
                self.config.username,
                self.config.password
            ])
            
            if auth_response.get("result") == "success":
                self.auth_token = auth_response.get("token")
                self.state = ConnectionState.CONNECTED
                self.connection_failures = 0
                logger.info("Successfully connected and authenticated to MSF RPC")
                return True
            else:
                logger.error(f"Authentication failed: {auth_response}")
                self.state = ConnectionState.FAILED
                return False
                
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            self.state = ConnectionState.FAILED
            self.connection_failures += 1
            return False
    
    async def disconnect(self):
        """Disconnect from the RPC server."""
        if self.auth_token:
            try:
                await self._rpc_call("auth.logout", [self.auth_token])
            except Exception as e:
                logger.warning(f"Error during logout: {e}")
        
        self.auth_token = None
        self.state = ConnectionState.DISCONNECTED
        logger.info("Disconnected from MSF RPC")
    
    async def call(self, method: str, params: List[Any] = None, timeout: int = None) -> Dict[str, Any]:
        """
        Make an RPC call to the Metasploit server.
        
        Args:
            method: RPC method to call (e.g., 'core.version')
            params: Parameters for the method
            timeout: Optional timeout override
            
        Returns:
            Dict containing the response
        """
        if self.state != ConnectionState.CONNECTED:
            if not await self._ensure_connected():
                raise ConnectionError("Not connected to RPC server")
        
        # Add auth token to params
        if params is None:
            params = []
        
        if self.auth_token:
            params = [self.auth_token] + params
        
        try:
            response = await self._rpc_call(method, params, timeout)
            return response
        except Exception as e:
            logger.error(f"RPC call failed: {method} - {e}")
            # Try reconnecting on failure
            if self.state == ConnectionState.CONNECTED:
                asyncio.create_task(self._reconnect())
            raise
    
    async def execute_console_command(self, command: str, console_id: str = None) -> Dict[str, Any]:
        """
        Execute a command through the console API.
        
        Args:
            command: Command to execute
            console_id: Optional console ID, creates new console if not provided
            
        Returns:
            Dict containing command results
        """
        # Create console if needed
        if not console_id:
            console_response = await self.call("console.create")
            console_id = console_response.get("id")
            if not console_id:
                raise RuntimeError("Failed to create console")
        
        # Write command to console
        await self.call("console.write", [console_id, command + "\n"])
        
        # Wait a moment for command to execute
        await asyncio.sleep(0.5)
        
        # Read output
        output_response = await self.call("console.read", [console_id])
        
        return {
            "console_id": console_id,
            "command": command,
            "output": output_response.get("data", ""),
            "busy": output_response.get("busy", False)
        }
    
    async def _rpc_call(self, method: str, params: List[Any] = None, timeout: int = None) -> Dict[str, Any]:
        """
        Make a raw RPC call to the server.
        
        Args:
            method: RPC method
            params: Method parameters
            timeout: Optional timeout
            
        Returns:
            Dict containing response
        """
        if not self.session:
            raise ConnectionError("Session not initialized")
        
        self.request_id += 1
        
        # Prepare request
        request_data = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or [],
            "id": self.request_id
        }
        
        # Determine URL
        protocol = "https" if self.config.ssl else "http"
        url = f"{protocol}://{self.config.host}:{self.config.port}/api/1.0/rpc"
        
        # Make request
        try:
            async with self.session.post(
                url,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=timeout or self.config.timeout)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    if "error" in result:
                        raise RuntimeError(f"RPC Error: {result['error']}")
                    return result.get("result", {})
                else:
                    raise RuntimeError(f"HTTP Error: {response.status}")
                    
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Connection error: {e}")
        except asyncio.TimeoutError:
            raise TimeoutError("RPC call timed out")
    
    async def _start_msfrpcd(self) -> bool:
        """Start the msfrpcd daemon."""
        logger.info("Starting msfrpcd daemon...")
        
        # Check if msfrpcd is available
        msfrpcd_path = "/usr/bin/msfrpcd"
        if not os.path.exists(msfrpcd_path):
            msfrpcd_path = "msfrpcd"  # Try in PATH
        
        try:
            # Start msfrpcd
            cmd = [
                msfrpcd_path,
                "-U", self.config.username,
                "-P", self.config.password,
                "-p", str(self.config.port),
                "-a", self.config.host,
                "-f"  # Run in foreground for process management
            ]
            
            if not self.config.ssl:
                cmd.append("-n")  # Disable SSL
            
            self.msfrpcd_process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait longer for server to start and check multiple times
            for i in range(10):  # Try for up to 10 seconds
                await asyncio.sleep(1)
                
                # Check if process is still running
                if self.msfrpcd_process.returncode is not None:
                    stdout, stderr = await self.msfrpcd_process.communicate()
                    logger.error(f"msfrpcd exited early: stdout={stdout.decode()}, stderr={stderr.decode()}")
                    return False
                
                # Check if server is accessible
                if await self._check_rpc_server():
                    logger.info("msfrpcd started successfully and is accessible")
                    return True
            
            logger.error("msfrpcd started but is not accessible after 10 seconds")
            return False
                
        except Exception as e:
            logger.error(f"Error starting msfrpcd: {e}")
            return False
    
    async def _stop_msfrpcd(self):
        """Stop the msfrpcd daemon."""
        if self.msfrpcd_process:
            logger.info("Stopping msfrpcd daemon...")
            try:
                # Try graceful shutdown first
                self.msfrpcd_process.terminate()
                await asyncio.wait_for(self.msfrpcd_process.wait(), timeout=10)
            except asyncio.TimeoutError:
                # Force kill if needed
                self.msfrpcd_process.kill()
                await self.msfrpcd_process.wait()
            
            self.msfrpcd_process = None
            logger.info("msfrpcd stopped")
    
    async def _check_rpc_server(self) -> bool:
        """Check if RPC server is accessible."""
        try:
            # Try a simple version call without auth
            protocol = "https" if self.config.ssl else "http"
            url = f"{protocol}://{self.config.host}:{self.config.port}/api/1.0/rpc"
            
            request_data = {
                "jsonrpc": "2.0",
                "method": "core.version",
                "params": [],
                "id": 1
            }
            
            async with self.session.post(
                url,
                json=request_data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status in [200, 401]  # 401 means server is running but needs auth
                
        except Exception:
            return False
    
    async def _ensure_connected(self) -> bool:
        """Ensure we have a valid connection."""
        if self.state == ConnectionState.CONNECTED and self.auth_token:
            # Test connection with a simple call
            try:
                await self._rpc_call("core.version", [self.auth_token])
                return True
            except Exception:
                logger.warning("Connection test failed, attempting reconnect")
                self.state = ConnectionState.DISCONNECTED
        
        # Try to reconnect
        return await self.connect()
    
    async def _reconnect(self):
        """Attempt to reconnect to the server."""
        if self.state == ConnectionState.RECONNECTING:
            return  # Already reconnecting
        
        self.state = ConnectionState.RECONNECTING
        logger.info("Attempting to reconnect...")
        
        for attempt in range(self.config.max_retries):
            try:
                await asyncio.sleep(self.config.retry_delay)
                if await self.connect():
                    logger.info("Reconnection successful")
                    return
                else:
                    logger.warning(f"Reconnection attempt {attempt + 1} failed")
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} error: {e}")
        
        logger.error("All reconnection attempts failed")
        self.state = ConnectionState.FAILED
    
    async def _health_check_loop(self):
        """Continuous health checking loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if self.state == ConnectionState.CONNECTED:
                    try:
                        # Simple health check
                        await self._rpc_call("core.version", [self.auth_token])
                        self.last_health_check = time.time()
                        self.connection_failures = 0
                    except Exception as e:
                        logger.warning(f"Health check failed: {e}")
                        self.connection_failures += 1
                        
                        if self.connection_failures >= 3:
                            logger.error("Multiple health check failures, attempting reconnect")
                            asyncio.create_task(self._reconnect())
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    @property
    def is_connected(self) -> bool:
        """Check if currently connected."""
        return self.state == ConnectionState.CONNECTED and self.auth_token is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current connection status."""
        return {
            "state": self.state.value,
            "connected": self.is_connected,
            "auth_token": bool(self.auth_token),
            "connection_failures": self.connection_failures,
            "last_health_check": self.last_health_check,
            "config": {
                "host": self.config.host,
                "port": self.config.port,
                "ssl": self.config.ssl
            }
        }