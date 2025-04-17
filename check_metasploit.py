#!/usr/bin/env python3

"""
Utility to check Metasploit installation and database connection
with better error handling and timeout management.
"""

import os
import sys
import asyncio
import shutil
import logging
import subprocess
from typing import Dict, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import the sudo helper
try:
    from sudo_helper import SudoHelper
    HAVE_SUDO_HELPER = True
    sudo_helper = SudoHelper()
except ImportError:
    HAVE_SUDO_HELPER = False
    sudo_helper = None
    logger.warning("sudo_helper module not found, will not use sudo helper functionality")

class MetasploitChecker:
    """
    Checks Metasploit installation and database connection
    with better error handling
    """
    
    def __init__(self, msfconsole_path=None, timeout=30):
        """
        Initialize the checker with paths to executables
        
        Args:
            msfconsole_path: Path to msfconsole executable
            timeout: Default timeout in seconds
        """
        # Find msfconsole if not specified
        self.msfconsole_path = msfconsole_path or shutil.which("msfconsole")
        if not self.msfconsole_path:
            self.msfconsole_path = "/usr/bin/msfconsole"  # Default path
            
        self.timeout = timeout
        
    async def check_installation(self) -> Tuple[bool, str]:
        """
        Check if Metasploit is installed and accessible
        
        Returns:
            Tuple of (success, message)
        """
        if not os.path.exists(self.msfconsole_path):
            return False, f"msfconsole not found at {self.msfconsole_path}"
            
        # Try to get version
        try:
            version_result = await self.get_version()
            if version_result["success"]:
                return True, f"Metasploit installed: {version_result.get('version', 'Unknown version')}"
            else:
                return False, f"Metasploit found but couldn't get version: {version_result.get('error', 'Unknown error')}"
        except Exception as e:
            return False, f"Error checking Metasploit installation: {str(e)}"
            
    async def get_version(self) -> Dict[str, Any]:
        """
        Get Metasploit Framework version with timeout handling
        
        Returns:
            Dict with version information or error
        """
        try:
            cmd = [self.msfconsole_path, "-v"]
            
            # Create process with asyncio
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for process with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.timeout
                )
                
                stdout_text = stdout.decode('utf-8', errors='replace')
                stderr_text = stderr.decode('utf-8', errors='replace')
                
                # Check for version string in output
                import re
                version_match = re.search(r'Framework: (\d+\.\d+\.\d+[-\w]*)', stdout_text)
                if version_match:
                    version = version_match.group(1)
                else:
                    version = "Unknown"
                    
                return {
                    "success": True,
                    "version": version,
                    "full_output": stdout_text
                }
                
            except asyncio.TimeoutError:
                # Kill the process if it's still running
                if process.returncode is None:
                    process.kill()
                return {
                    "success": False,
                    "error": f"Timeout after {self.timeout} seconds"
                }
                
        except Exception as e:
            logger.error(f"Error getting Metasploit version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def check_db_status(self) -> Dict[str, Any]:
        """
        Check if the Metasploit database is connected with timeout handling
        
        Returns:
            Dict with database status or error
        """
        try:
            # Create a temporary resource script
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.rc') as tmp:
                tmp.write("db_status\n")
                tmp.write("exit\n")
                tmp_filename = tmp.name
                
            try:
                # Run msfconsole with the resource script
                cmd = [self.msfconsole_path, "-q", "-r", tmp_filename]
                
                # Create process with asyncio
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Wait for process with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.timeout
                    )
                    
                    stdout_text = stdout.decode('utf-8', errors='replace')
                    stderr_text = stderr.decode('utf-8', errors='replace')
                    
                    # Check for database connected string
                    db_connected = "connected" in stdout_text.lower()
                    
                    return {
                        "success": True,
                        "db_connected": db_connected,
                        "output": stdout_text
                    }
                    
                except asyncio.TimeoutError:
                    # Kill the process if it's still running
                    if process.returncode is None:
                        process.kill()
                    return {
                        "success": False,
                        "error": f"Database check timed out after {self.timeout} seconds"
                    }
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_filename)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file: {e}")
                    
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            return {
                "success": False,
                "error": str(e)
            }
            
    def run_db_init(self, timeout=60) -> Dict[str, Any]:
        """
        Initialize the Metasploit database with timeout handling
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Dict with initialization result or error
        """
        try:
            # Use the sudo helper if available
            if HAVE_SUDO_HELPER and sudo_helper:
                logger.info("Using sudo helper to initialize database")
                return sudo_helper.run_sudo_command(["msfdb", "init"], timeout=timeout)
            
            # Fall back to subprocess.run with timeout for synchronous execution
            cmd = ["sudo", "msfdb", "init"]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                text=True
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": f"Database initialization timed out after {timeout} seconds"
            }
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def run_db_reinit(self, timeout=60) -> Dict[str, Any]:
        """
        Reinitialize the Metasploit database with timeout handling
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Dict with reinitialization result or error
        """
        try:
            # First, try to stop the database
            if HAVE_SUDO_HELPER and sudo_helper:
                stop_result = sudo_helper.run_sudo_command(["msfdb", "stop"], timeout=timeout)
                if not stop_result["success"]:
                    logger.warning(f"Failed to stop database: {stop_result.get('error', 'Unknown error')}")
            else:
                stop_cmd = ["sudo", "msfdb", "stop"]
                try:
                    subprocess.run(stop_cmd, timeout=timeout, check=False, text=True)
                except Exception:
                    logger.warning("Failed to stop database")
            
            # Wait a bit for the database to stop
            import time
            time.sleep(2)
            
            # Now reinitialize
            return self.run_db_init(timeout)
            
        except Exception as e:
            logger.error(f"Error reinitializing database: {e}")
            return {
                "success": False,
                "error": str(e)
            }

async def main():
    """
    Main function to check Metasploit installation and database
    """
    print("Checking Metasploit installation and database...")
    
    checker = MetasploitChecker()
    
    # Check installation
    installed, install_msg = await checker.check_installation()
    print(f"Installation status: {install_msg}")
    
    if installed:
        # Check database status
        db_result = await checker.check_db_status()
        if db_result["success"]:
            if db_result.get("db_connected", False):
                print("Database status: Connected")
            else:
                print("Database status: Not connected")
                print("Would you like to initialize the database? (y/n)")
                response = input("> ")
                if response.lower() == 'y':
                    print("Initializing database (this may take a while)...")
                    init_result = checker.run_db_init()
                    if init_result["success"]:
                        print("Database initialization successful")
                    else:
                        print(f"Database initialization failed: {init_result.get('error', 'Unknown error')}")
                        print("Would you like to reinitialize the database? (y/n)")
                        reinit = input("> ")
                        if reinit.lower() == 'y':
                            print("Reinitializing database...")
                            reinit_result = checker.run_db_reinit()
                            if reinit_result["success"]:
                                print("Database reinitialization successful")
                            else:
                                print(f"Database reinitialization failed: {reinit_result.get('error', 'Unknown error')}")
        else:
            print(f"Database status check failed: {db_result.get('error', 'Unknown error')}")
    
if __name__ == "__main__":
    asyncio.run(main())
