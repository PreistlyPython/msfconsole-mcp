# MSFConsole MCP Resources

This directory contains the MSFConsole MCP (Model Context Protocol) server, which provides:

1. Tools for interacting with Metasploit Framework through MCP
2. Prompts for common penetration testing workflows
3. Resources with Metasploit documentation and reference guides

## How to Use Resources and Prompts

The MSFConsole MCP server has been split into two components:

1. Main Server (`msfconsole_mcp.py`) - Provides tools for interacting with Metasploit
2. Resources Server (`register_resources.py`) - Provides prompts and documentation resources

### Running the Resources Server

To load the prompts and resources, run:

```bash
/home/dell/coding/mcp/venv/bin/python /home/dell/coding/mcp/msfconsole/register_resources.py
```

Connect to this server in the MCP Inspector to view and use the prompts and resources.

### Running the Main Server

To interact with Metasploit, run:

```bash
/home/dell/coding/mcp/venv/bin/python /home/dell/coding/mcp/msfconsole/msfconsole_mcp.py
```

Connect to this server in the MCP Inspector to use the Metasploit tools.

## Adding New Prompts or Resources

All prompts and resources are defined in the `mcp_config.json` file. To add new ones:

1. Edit `mcp_config.json`
2. Add entries to the "prompts" or "resources" arrays
3. Restart the resources server

For example:

```json
{
  "prompts": [
    {
      "title": "New Prompt",
      "description": "Description of the new prompt",
      "content": "This is the content of the new prompt that will be sent to the LLM"
    }
  ],
  "resources": [
    {
      "title": "New Resource",
      "description": "Description of the new resource",
      "content": "This is the content of the new resource that will be available to the LLM"
    }
  ]
}
```

## Troubleshooting

- If no prompts or resources appear in the MCP Inspector, ensure that you're connected to the resources server (`register_resources.py`), not the main server.
- The resources server runs separately from the main MCP server.
