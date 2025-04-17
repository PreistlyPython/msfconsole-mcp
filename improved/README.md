# Improved Metasploit Framework Console MCP

An enhanced and more reliable Metasploit Framework integration for MCP (Model, Controller, Processor) that allows AI assistants to interact with Metasploit through a structured API.

## Key Improvements

- Robust database initialization and connection handling
- More reliable command execution using resource scripts
- Better error handling and timeout management
- Enhanced progress reporting
- Improved parsing of command outputs
- Comprehensive documentation
- Automatic cleanup of temporary files

## Features

- Execute msfconsole commands with improved reliability
- Search for Metasploit modules
- Manage workspaces with proper database checks
- Run scans against target hosts
- Manage database operations with structured data output
- Generate payloads with msfvenom
- Manage and interact with sessions
- Access detailed module information
- Browse built-in documentation

## Prerequisites

- Python 3.8+
- Metasploit Framework
- MCP SDK
- PostgreSQL (for Metasploit database)

## Installation

1. Make sure the parent directory has a Python virtual environment:
```bash
cd ..
./fix_python_version.sh  # If needed to set up a compatible environment
```

2. Run the installation script:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the MCP server with database initialization:
```bash
./launch_msfconsole_mcp_improved.sh
```

## Available Tools

This MCP provides the following tools:

- `get_msf_version`: Get the installed Metasploit Framework version
- `run_msf_command`: Execute a command in msfconsole
- `search_modules`: Search for modules in the Metasploit Framework
- `manage_workspaces`: List and manage Metasploit workspaces
- `run_scan`: Run a scan against target hosts
- `manage_database`: Manage the Metasploit database
- `manage_sessions`: List and manage Metasploit sessions
- `generate_payload`: Generate a payload using msfvenom
- `show_module_info`: Show detailed information about a Metasploit module
- `browse_documentation`: Access built-in documentation on Metasploit usage

## Architecture

This improved MCP uses a more reliable execution strategy:

1. **Database Initialization**: The launch script ensures the Metasploit database is properly initialized before starting the MCP.

2. **Resource Script Execution**: Instead of maintaining a long-running msfconsole process, each command is executed in a separate process using resource scripts. This prevents hanging and provides more reliable timeout handling.

3. **SafeContext Wrapper**: A compatibility layer that ensures consistent progress reporting regardless of the MCP context implementation.

4. **Enhanced Output Parsing**: Better parsing of command outputs to provide structured data where available.

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs` directory
2. Ensure PostgreSQL is running: `systemctl status postgresql`
3. Try manually initializing the Metasploit database: `msfdb init`
4. Verify Metasploit can run standalone: `msfconsole -q -x "version; exit"`

## License

This project is licensed under the MIT License.

## Disclaimer

This tool is designed for legal security testing only. Always ensure you have permission before testing any system, and follow all applicable laws and regulations.
