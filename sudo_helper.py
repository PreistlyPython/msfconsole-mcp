#!/usr/bin/env python3

"""
Sudo Helper for Metasploit MCP
This module provides functions to handle sudo privileges for MCP commands.
"""

import os
import sys
import logging
import subprocess
import shutil
import getpass
from typing import Dict, Any, Optional, List, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='sudo_helper.log'
)
logger = logging.getLogger(__name__)

class SudoHelper:
    """
    Class to handle sudo privileges for Metasploit commands
    """
    
    def __init__(self, sudo_password: Optional[str] = None, use_pass: bool = True):
        """
        Initialize the SudoHelper
        
        Args:
            sudo_password: Optional sudo password (not recommended for production)
            use_pass: Whether to use the pass password manager
        """
        self.sudo_password = sudo_password
        self.use_pass = use_pass
        self.have_sudo = False
        
        # Check for required tools
        self.have_pass = shutil.which("pass") is not None
        self.have_sudo = shutil.which("sudo") is not None
        
        if use_pass and not self.have_pass:
            logger.warning("pass command not found, falling back to manual password entry")
            self.use_pass = False
            
        if not self.have_sudo:
            logger.error("sudo command not found, sudo helper cannot function")
            
    def setup_pass(self, gpg_key_id: str = None) -> bool:
        """
        Set up the pass password store
        
        Args:
            gpg_key_id: GPG key ID to use for pass
            
        Returns:
            bool: True if setup was successful
        """
        if not self.have_pass:
            logger.error("pass command not found, cannot set up")
            return False
            
        try:
            # Check if pass is already initialized
            result = subprocess.run(
                ["pass", "ls"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if result.returncode == 0:
                logger.info("pass already initialized")
                return True
                
            # Initialize pass if needed
            if gpg_key_id:
                init_cmd = ["pass", "init", gpg_key_id]
            else:
                # Try to get the default GPG key
                gpg_result = subprocess.run(
                    ["gpg", "--list-secret-keys", "--with-colons"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                if gpg_result.returncode != 0:
                    logger.error("Failed to list GPG keys")
                    return False
                    
                # Parse output to find the first secret key
                for line in gpg_result.stdout.splitlines():
                    if line.startswith("sec:"):
                        parts = line.split(":")
                        if len(parts) >= 5:
                            key_id = parts[4]
                            init_cmd = ["pass", "init", key_id]
                            break
                else:
                    logger.error("No GPG keys found")
                    return False
            
            # Run pass init
            init_result = subprocess.run(
                init_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            if init_result.returncode != 0:
                logger.error(f"Failed to initialize pass: {init_result.stderr}")
                return False
                
            logger.info("pass initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error setting up pass: {e}")
            return False
            
    def store_sudo_password(self) -> bool:
        """
        Store the sudo password in pass
        
        Returns:
            bool: True if password was stored successfully
        """
        if not self.have_pass or not self.use_pass:
            logger.error("pass not available or not configured to use it")
            return False
            
        try:
            # Prompt for the sudo password
            if not self.sudo_password:
                self.sudo_password = getpass.getpass("Enter sudo password to store: ")
                
            # Store the password
            store_cmd = ["pass", "insert", "-f", "sudo/password"]
            process = subprocess.Popen(
                store_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Write the password to stdin
            stdout, stderr = process.communicate(input=f"{self.sudo_password}\n{self.sudo_password}\n")
            
            if process.returncode != 0:
                logger.error(f"Failed to store sudo password: {stderr}")
                return False
                
            logger.info("Sudo password stored successfully")
            self.sudo_password = None  # Clear the password from memory
            return True
            
        except Exception as e:
            logger.error(f"Error storing sudo password: {e}")
            return False
            
    def create_askpass_script(self, script_path: str = None) -> Optional[str]:
        """
        Create a script to be used with SUDO_ASKPASS
        
        Args:
            script_path: Path to create the script (default: ~/sudo_askpass.sh)
            
        Returns:
            str: Path to created script, or None if failed
        """
        if not script_path:
            script_path = os.path.expanduser("~/sudo_askpass.sh")
            
        try:
            # Create the script
            with open(script_path, "w") as f:
                if self.use_pass and self.have_pass:
                    f.write("#!/bin/bash\npass show sudo/password\n")
                else:
                    f.write(f"#!/bin/bash\necho '{self.sudo_password}'\n")
                    
            # Make it executable
            os.chmod(script_path, 0o700)
            
            logger.info(f"Created askpass script at {script_path}")
            return script_path
            
        except Exception as e:
            logger.error(f"Error creating askpass script: {e}")
            return None
            
    def run_sudo_command(self, command: Union[str, List[str]], timeout: int = 60) -> Dict[str, Any]:
        """
        Run a command with sudo
        
        Args:
            command: Command to run (string or list)
            timeout: Timeout in seconds
            
        Returns:
            Dict with command result
        """
        if not self.have_sudo:
            return {"success": False, "error": "sudo not available"}
            
        try:
            # Convert command to list if it's a string
            if isinstance(command, str):
                cmd_list = command.split()
            else:
                cmd_list = command
                
            # Check if we should use SUDO_ASKPASS
            env = os.environ.copy()
            use_askpass = self.use_pass and self.have_pass
            
            if use_askpass:
                # Create temporary askpass script if needed
                askpass_script = self.create_askpass_script()
                if askpass_script:
                    env["SUDO_ASKPASS"] = askpass_script
                    sudo_cmd = ["sudo", "-A"] + cmd_list
                else:
                    # Fall back to regular sudo
                    sudo_cmd = ["sudo"] + cmd_list
            else:
                # Use pexpect if we have the password but no askpass method
                if self.sudo_password:
                    try:
                        import pexpect
                        
                        # Join the command for pexpect
                        cmd_str = "sudo " + " ".join(cmd_list)
                        
                        # Spawn the process
                        child = pexpect.spawn(cmd_str)
                        
                        # Expect the password prompt or EOF
                        i = child.expect(['password for.*:', pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)
                        
                        if i == 0:  # Password prompt
                            child.sendline(self.sudo_password)
                            child.expect(pexpect.EOF, timeout=timeout)
                            
                        # Get the output
                        output = child.before.decode('utf-8')
                        
                        return {
                            "success": True,
                            "stdout": output,
                            "stderr": "",
                            "returncode": 0
                        }
                    except ImportError:
                        logger.warning("pexpect not available, falling back to regular sudo")
                        sudo_cmd = ["sudo"] + cmd_list
                    except Exception as e:
                        logger.error(f"Error using pexpect: {e}")
                        return {"success": False, "error": str(e)}
                else:
                    # No password and no askpass, just use regular sudo
                    sudo_cmd = ["sudo"] + cmd_list
            
            # Run the command
            process = subprocess.run(
                sudo_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                timeout=timeout
            )
            
            return {
                "success": process.returncode == 0,
                "stdout": process.stdout,
                "stderr": process.stderr,
                "returncode": process.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout} seconds"}
        except Exception as e:
            logger.error(f"Error running sudo command: {e}")
            return {"success": False, "error": str(e)}

# Helper function to initialize the module
def initialize_sudo_helper(use_pass: bool = True, store_password: bool = False) -> SudoHelper:
    """
    Initialize the sudo helper
    
    Args:
        use_pass: Whether to use the pass password manager
        store_password: Whether to prompt for and store the sudo password
        
    Returns:
        SudoHelper: Initialized sudo helper
    """
    helper = SudoHelper(use_pass=use_pass)
    
    if use_pass and helper.have_pass:
        helper.setup_pass()
        
        if store_password:
            helper.store_sudo_password()
    
    return helper

if __name__ == "__main__":
    # Run the initialization process if called directly
    print("Initializing Sudo Helper for Metasploit MCP")
    
    use_pass = input("Use pass password manager? (y/n): ").lower() == 'y'
    store_password = input("Store sudo password? (y/n): ").lower() == 'y'
    
    helper = initialize_sudo_helper(use_pass, store_password)
    
    # Test a simple command
    print("Testing sudo command execution...")
    result = helper.run_sudo_command(["echo", "Hello, sudo!"])
    
    if result["success"]:
        print(f"Command succeeded: {result['stdout']}")
    else:
        print(f"Command failed: {result.get('error', result.get('stderr', 'Unknown error'))}")
    
    print("Setup complete.")
