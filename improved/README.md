# Improved MSFConsole MCP

An enhanced version of the Metasploit Framework Console Model Context Protocol (MCP) integration. This improved version provides better error handling, compatibility with different MCP SDK versions, and a more robust architecture.

## Features

- **Robust Command Execution**: Uses resource scripts for reliable MSF command execution
- **Cross-Version Compatibility**: Works with different versions of the MCP SDK
- **Progress Reporting**: Comprehensive and reliable progress tracking during long operations
- **Error Handling**: Detailed error information with graceful degradation
- **Automatic API Detection**: Dynamically adapts to available methods and signatures

## Project Structure

- **msfconsole_mcp_improved.py**: Main MCP server implementation
- **msf_execution.py**: Core class for executing Metasploit commands
- **safe_context.py**: Compatibility layer for different MCP Context APIs
- **config.py**: Configuration settings
- **test_safe_context.py**: Test suite for verifying compatibility
- **launch_msfconsole_mcp_improved.sh**: Launch script for the MCP server

## Recent Improvements

The latest version (0.3.0) includes significant improvements to ensure compatibility with different MCP SDK versions:

1. **Enhanced SafeContext**: 
   - Moved to a separate module for better maintainability
   - Added dynamic signature detection for Context methods
   - Improved error handling and fallback mechanisms
   - Enhanced progress reporting with normalization

2. **Comprehensive Testing**:
   - Added a robust test suite for verifying compatibility
   - Tests multiple API versions and error scenarios
   - Ensures consistent behavior across different environments

3. **Documentation**:
   - Added detailed code documentation
   - Created a comprehensive changelog
   - Improved README with usage instructions

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

## SafeContext Compatibility

The SafeContext module provides compatibility with different MCP SDK versions:

- **MCP 1.x**: Uses `report_progress(current, total)`
- **MCP 2.x**: Uses `report_progress(current, total, message)`
- **Alternative styles**: Supports `progress(message, percentage)`
- **Missing methods**: Falls back to logging

## Testing

To run the test suite:

```bash
python test_safe_context.py
```

This will verify that the SafeContext implementation correctly handles:
- Different MCP Context API versions
- Missing methods
- Error conditions
- Parameter mismatches

## Changelog

See [CHANGELOG.md](./CHANGELOG.md) for a history of changes to this project.
