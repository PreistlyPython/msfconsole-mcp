# Improved MSFConsole MCP

This is an enhanced version of the Metasploit Framework Console Model Context Protocol (MCP) integration. The improved version provides better error handling, compatibility with different MCP SDK versions, and a more robust architecture.

## Features

- **Robust Command Execution**: Uses resource scripts for reliable MSF command execution
- **Progress Reporting**: Comprehensive progress tracking during long operations
- **Error Handling**: Detailed error information with graceful degradation
- **MCP Compatibility**: Works with different versions of the MCP SDK

## Recent Improvements

- Fixed compatibility issues with different MCP Context APIs
- Enhanced progress reporting with dynamic signature detection
- Separated SafeContext into its own module for better maintainability
- Added comprehensive test suite for verifying compatibility

## Project Structure

- `msfconsole_mcp_improved.py`: Main MCP server implementation
- `msf_execution.py`: Core class for executing Metasploit commands
- `safe_context.py`: Compatibility layer for different MCP Context APIs
- `config.py`: Configuration settings for the MCP
- `test_safe_context.py`: Test suite for the SafeContext module
- Various shell scripts for environment setup and server launching

## Usage

1. Ensure Metasploit Framework is installed and the database is initialized
2. Run the launch script to start the MCP server:

```bash
./launch_msfconsole_mcp_improved.sh
```

3. The MCP tools will be available through the Claude Desktop interface

## Available Tools

- `get_msf_version`: Retrieve Metasploit Framework version
- `run_msf_command`: Execute arbitrary MSF commands
- `search_modules`: Search for Metasploit modules
- `manage_workspaces`: Manage MSF workspaces
- `run_scan`: Execute different types of scans
- `manage_database`: Perform database operations
- `manage_sessions`: List and manage active sessions
- `generate_payload`: Generate payloads using msfvenom
- `show_module_info`: Get detailed information about modules
- `browse_documentation`: Access MSF documentation

## Testing

To test the SafeContext implementation:

```bash
python test_safe_context.py
```

This will verify that the SafeContext correctly handles different MCP Context APIs.

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a history of changes to this project.
