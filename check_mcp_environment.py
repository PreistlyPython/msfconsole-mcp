#!/usr/bin/env python3

"""
MCP Environment Checker for MSFconsole MCP
------------------------------------------
This script checks the MCP environment and provides diagnostic information
to help resolve common issues.
"""

import os
import sys
import importlib
import importlib.metadata
import importlib.util
import subprocess
import shutil
import platform

# Define color codes for pretty output
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"

def print_header(text):
    """Print a section header"""
    print(f"\n{BOLD}{BLUE}{'=' * 60}{RESET}")
    print(f"{BOLD}{BLUE}{text.center(60)}{RESET}")
    print(f"{BOLD}{BLUE}{'=' * 60}{RESET}")

def print_success(text):
    """Print a success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_warning(text):
    """Print a warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_error(text):
    """Print an error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    """Print an info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

def check_python_version():
    """Check the Python version"""
    print_header("Python Environment")
    
    # Print Python version
    py_version = platform.python_version()
    major, minor, patch = map(int, py_version.split('.'))
    
    print_info(f"Python version: {py_version}")
    
    if major < 3 or (major == 3 and minor < 7):
        print_error(f"Python version {py_version} is too old. MCP requires Python 3.7+")
    else:
        print_success(f"Python version {py_version} is supported")
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if in_venv:
        print_success(f"Running in virtual environment: {sys.prefix}")
    else:
        print_warning("Not running in a virtual environment")
    
    # Print system path
    print_info("Python system path:")
    for i, path in enumerate(sys.path):
        print(f"  {i+1}. {path}")

def check_required_packages():
    """Check if required packages are installed"""
    print_header("Required Packages")
    
    required_packages = {
        "mcp": "0.1.0",  # Minimum version
        "typing-extensions": "4.0.0",
        "asyncio": "3.4.3"
    }
    
    all_ok = True
    
    for package, min_version in required_packages.items():
        try:
            version = importlib.metadata.version(package)
            print_info(f"Package {package}: version {version}")
            
            # Simple version check (this is basic, could be enhanced)
            if version.split('.')[0] < min_version.split('.')[0]:
                print_warning(f"Package {package} version {version} may be too old (min: {min_version})")
                all_ok = False
            else:
                print_success(f"Package {package} meets minimum version requirement")
                
        except importlib.metadata.PackageNotFoundError:
            print_error(f"Required package {package} not found")
            all_ok = False
    
    if all_ok:
        print_success("All required packages are installed")
    else:
        print_warning("Some required packages are missing or outdated")
        print_info("Try running: pip install -r requirements.txt")

def check_mcp_import():
    """Check if MCP can be imported"""
    print_header("MCP SDK Import Test")
    
    try:
        import mcp
        print_success(f"Successfully imported mcp package from {mcp.__file__}")
        
        try:
            version = mcp.__version__
            print_info(f"MCP SDK version: {version}")
        except AttributeError:
            print_warning("Could not determine MCP SDK version")
        
        try:
            from mcp.server.fastmcp import FastMCP, Context
            print_success("Successfully imported FastMCP and Context")
            
            # Try creating a FastMCP instance
            try:
                test_mcp = FastMCP("test", version="0.1.0")
                print_success("Successfully created FastMCP instance")
            except Exception as e:
                print_error(f"Error creating FastMCP instance: {e}")
                
        except ImportError as e:
            print_error(f"Failed to import from mcp.server.fastmcp: {e}")
            
    except ImportError as e:
        print_error(f"Failed to import mcp package: {e}")
        # Try to find mcp in installed packages
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
            if "mcp" in result.stdout:
                print_info("mcp package is installed but not importable")
                print_warning("Check your Python path and virtual environment")
            else:
                print_info("mcp package is not installed")
                print_warning("Run: pip install 'mcp[cli]>=0.1.0'")
        except Exception:
            pass

def check_metasploit():
    """Check if Metasploit is installed"""
    print_header("Metasploit Framework")
    
    # Check for msfconsole in PATH
    msf_path = shutil.which("msfconsole")
    
    if msf_path:
        print_success(f"Found msfconsole in PATH: {msf_path}")
        
        # Try to get version
        try:
            result = subprocess.run([msf_path, "-v"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version_line = result.stdout.strip().split('\n')[0] if result.stdout else "Unknown"
                print_info(f"Metasploit version: {version_line}")
            else:
                print_warning("Could not determine Metasploit version")
                print_info(f"Error: {result.stderr.strip()}")
        except subprocess.TimeoutExpired:
            print_warning("Command timed out when checking Metasploit version")
        except Exception as e:
            print_warning(f"Error checking Metasploit version: {e}")
    else:
        print_warning("msfconsole not found in PATH")
        print_info("The MCP will have limited functionality without Metasploit")
        
        # Try to find in common locations
        common_locations = [
            "/usr/bin/msfconsole",
            "/usr/local/bin/msfconsole",
            "/opt/metasploit-framework/bin/msfconsole"
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                print_info(f"Found msfconsole at: {location}")
                print_info(f"You can configure this path in your config.py")
                break

def check_project_files():
    """Check if all required project files exist"""
    print_header("MSFconsole MCP Project Files")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        "msfconsole_mcp.py",
        "safe_context.py",
        "launch_msfconsole_mcp.sh",
        "requirements.txt",
        "doc_tools.py"
    ]
    
    all_ok = True
    
    for file in required_files:
        file_path = os.path.join(script_dir, file)
        if os.path.exists(file_path):
            print_success(f"Found required file: {file}")
            
            # Check if scripts are executable
            if file.endswith('.sh') or file.endswith('.py'):
                if os.access(file_path, os.X_OK):
                    print_success(f"File {file} is executable")
                else:
                    print_warning(f"File {file} is not executable")
                    print_info(f"Run: chmod +x {file_path}")
                    all_ok = False
        else:
            print_error(f"Missing required file: {file}")
            all_ok = False
    
    # Check for config.py
    config_path = os.path.join(script_dir, "config.py")
    if os.path.exists(config_path):
        print_info(f"Found config.py (custom configuration)")
    else:
        print_info("No config.py found (using default configuration)")
    
    # Check for logs directory
    logs_dir = os.path.join(script_dir, "logs")
    if os.path.exists(logs_dir) and os.path.isdir(logs_dir):
        print_success("Found logs directory")
    else:
        print_warning("Missing logs directory")
        print_info("The script will create it when needed")
    
    if all_ok:
        print_success("All required project files are present")
    else:
        print_warning("Some required project files are missing")

def check_environment_variables():
    """Check if relevant environment variables are set"""
    print_header("Environment Variables")
    
    relevant_vars = [
        "PYTHONPATH",
        "VIRTUAL_ENV",
        "PATH"
    ]
    
    for var in relevant_vars:
        if var in os.environ:
            value = os.environ[var]
            print_info(f"{var}={value}")
        else:
            print_info(f"{var} is not set")
    
    # Check for PYTHONPATH issues
    if "PYTHONPATH" in os.environ:
        venv_lib = os.path.join(sys.prefix, "lib")
        if venv_lib not in os.environ["PYTHONPATH"]:
            print_warning("PYTHONPATH does not include the virtual environment library path")
            print_info(f"Consider adding {venv_lib} to PYTHONPATH")

def suggest_fixes(issues):
    """Suggest fixes for common issues"""
    print_header("Suggested Fixes")
    
    if not issues:
        print_success("No issues detected! Your environment looks good.")
        return
    
    for issue in issues:
        print_warning(issue["problem"])
        print_info(f"Solution: {issue['solution']}")
        print()

def main():
    """Main function"""
    print_header("MCP Environment Checker")
    print_info(f"Running on: {platform.platform()}")
    print_info(f"Current directory: {os.getcwd()}")
    
    # Run checks
    check_python_version()
    check_required_packages()
    check_mcp_import()
    check_metasploit()
    check_project_files()
    check_environment_variables()
    
    # List common issues and solutions
    issues = []
    
    # Check for common issues and add to the list
    
    # PYTHONPATH issue
    if "PYTHONPATH" not in os.environ or not any(p.endswith("site-packages") for p in os.environ.get("PYTHONPATH", "").split(os.pathsep)):
        issues.append({
            "problem": "PYTHONPATH does not include site-packages directory",
            "solution": "Set PYTHONPATH to include the site-packages directory of your virtual environment"
        })
    
    # Virtual env issue
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        issues.append({
            "problem": "Not running in a virtual environment",
            "solution": "Activate the virtual environment with 'source venv/bin/activate'"
        })
    
    # MCP import issue
    try:
        import mcp
    except ImportError:
        issues.append({
            "problem": "Cannot import mcp package",
            "solution": "Install the MCP SDK with 'pip install \"mcp[cli]>=0.1.0\"'"
        })
    
    suggest_fixes(issues)
    
    print_header("Summary")
    if issues:
        print_warning(f"Found {len(issues)} potential issues that may affect MCP operation")
        print_info("Run the launch script with: ./launch_msfconsole_mcp.sh")
    else:
        print_success("Your environment looks good! You should be able to run the MCP successfully.")
        print_info("Run the launch script with: ./launch_msfconsole_mcp.sh")

if __name__ == "__main__":
    main()
