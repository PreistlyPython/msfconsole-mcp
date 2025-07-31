#!/usr/bin/env python3
"""
Metasploit Initialization Helper
Handles database and service initialization
"""

import asyncio
import subprocess
import logging
import os
import time

logger = logging.getLogger(__name__)

class MSFInitializer:
    """Handles Metasploit Framework initialization"""
    
    def __init__(self):
        self.db_initialized = False
        self.msfconsole_ready = False
        
    async def ensure_database_ready(self) -> bool:
        """Ensure Metasploit database is ready"""
        try:
            # Check database status
            result = subprocess.run(['msfdb', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            
            if "Database started" in result.stdout:
                logger.info("Metasploit database is running")
                self.db_initialized = True
                return True
            else:
                logger.warning("Database not running, attempting to start...")
                return await self._start_database()
                
        except Exception as e:
            logger.error(f"Error checking database status: {e}")
            return False
    
    async def _start_database(self) -> bool:
        """Start the Metasploit database"""
        try:
            logger.info("Starting Metasploit database...")
            result = subprocess.run(['msfdb', 'start'], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Database started successfully")
                self.db_initialized = True
                return True
            else:
                logger.error(f"Failed to start database: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting database: {e}")
            return False
    
    async def warm_up_msfconsole(self) -> bool:
        """Warm up msfconsole for faster subsequent launches"""
        try:
            logger.info("Warming up msfconsole...")
            
            # Create a simple version check script
            script_content = "version\nexit\n"
            
            # Use a temporary file for the warm-up
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rc', delete=False) as f:
                f.write(script_content)
                script_path = f.name
            
            try:
                # Run the warm-up command with a reasonable timeout
                process = await asyncio.create_subprocess_exec(
                    'msfconsole', '-q', '-r', script_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), timeout=60
                )
                
                if process.returncode == 0:
                    logger.info("msfconsole warm-up completed successfully")
                    self.msfconsole_ready = True
                    return True
                else:
                    logger.warning(f"msfconsole warm-up had issues: {stderr.decode()}")
                    return False
                    
            finally:
                # Clean up temp file
                try:
                    os.unlink(script_path)
                except:
                    pass
                    
        except asyncio.TimeoutError:
            logger.error("msfconsole warm-up timed out")
            return False
        except Exception as e:
            logger.error(f"Error warming up msfconsole: {e}")
            return False
    
    async def initialize_all(self) -> bool:
        """Initialize all Metasploit components"""
        logger.info("Starting Metasploit initialization...")
        
        # Step 1: Ensure database is ready
        if not await self.ensure_database_ready():
            logger.error("Failed to initialize database")
            return False
        
        # Step 2: Warm up msfconsole
        if not await self.warm_up_msfconsole():
            logger.warning("msfconsole warm-up failed, but continuing...")
        
        logger.info("Metasploit initialization completed")
        return True

# Global initializer instance
_initializer = None

async def get_initializer() -> MSFInitializer:
    """Get or create the global initializer"""
    global _initializer
    if _initializer is None:
        _initializer = MSFInitializer()
        await _initializer.initialize_all()
    return _initializer

if __name__ == "__main__":
    # Test the initializer
    import logging
    logging.basicConfig(level=logging.INFO)
    
    async def test():
        init = MSFInitializer()
        success = await init.initialize_all()
        print(f"Initialization {'successful' if success else 'failed'}")
    
    asyncio.run(test())