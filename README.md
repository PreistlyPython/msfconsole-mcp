# Metasploit Framework Console MCP

A Metasploit Framework Console MCP (Model, Controller, Processor) integration that allows AI assistants to interact with Metasploit Framework through a structured API. This integration makes Metasploit's powerful penetration testing capabilities accessible to AI systems in a secure and controlled way.

## Features

- Execute msfconsole commands programmatically
- Search for modules
- Manage workspaces
- Run scans
- Manage database operations
- Generate payloads with msfvenom
- Manage sessions
- Show detailed module information

## Prerequisites

- Python 3.8+
- Metasploit Framework
- MCP SDK

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/msfconsole-mcp.git
cd msfconsole-mcp
```

2. Run the installation script:
```bash
chmod +x install.sh
./install.sh
```

The script will:
- Check for Python 3.8+
- Install required Python dependencies
- Check if Metasploit Framework is installed and offer to install it if it's not
- Install the MCP SDK

## Usage

Start the MCP server:
```bash
./start_mcp.sh
```

### Available Tools

- `get_msf_version`: Get the installed Metasploit Framework version
- `run_msf_command`: Execute a command in msfconsole
- `search_modules`: Search for modules in the Metasploit Framework
- `manage_workspaces`: List and manage Metasploit workspaces
- `run_scan`: Run a scan against target hosts
- `manage_database`: Manage the Metasploit database
- `manage_sessions`: List and manage Metasploit sessions
- `generate_payload`: Generate a payload using msfvenom
- `show_module_info`: Show detailed information about a Metasploit module

## Configuration

You can customize the behavior by creating a `config.py` file. See the code for configuration options.

## Security Considerations

This MCP enforces security measures such as:
- Command validation
- Timeout limits
- Disallowed modules filtering

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is designed for legal security testing only. Always ensure you have permission before testing any system, and follow all applicable laws and regulations.
