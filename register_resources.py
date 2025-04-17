#!/usr/bin/env python3

"""
Script to register prompts and resources with the MSFConsole MCP
"""

import os
import json
import sys
from pathlib import Path
import asyncio

# Add the msfconsole directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Import the needed MCP modules
from mcp.server.fastmcp import FastMCP, Context


def register_prompts_and_resources(server):
    """Register prompts and resources with the MCP server"""
    config_path = os.path.join(script_dir, "mcp_config.json")
    
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            
        # Register prompts
        for prompt_data in config.get("prompts", []):
            name = prompt_data.get("title")
            description = prompt_data.get("description")
            content = prompt_data.get("content")
            
            # Define a prompt function that returns the content as a message
            @server.prompt(name=name, description=description)
            def generate_prompt_fn():
                return [{"role": "user", "content": content}]
            
            print(f"Registered prompt: {name}")
            
        # Register resources
        for resource_data in config.get("resources", []):
            name = resource_data.get("title")
            description = resource_data.get("description")
            content = resource_data.get("content")
            
            # Convert name to URI format
            uri = f"resource://{name.lower().replace(' ', '-')}"
            
            @server.resource(uri=uri, name=name, description=description)
            def get_resource():
                return content
            
            print(f"Registered resource: {name} at {uri}")
            
        print("All prompts and resources registered successfully")
        
    except Exception as e:
        print(f"Error registering prompts and resources: {e}")
        return False
        
    return True


def create_dynamic_mcp():
    """Create a new FastMCP server with prompts and resources"""
    # Create a new FastMCP server
    server = FastMCP(name="MSFConsole Resources", version="0.1.0")
    
    # Register prompts and resources
    if register_prompts_and_resources(server):
        print("Prompts and resources registered. Run with:")
        print("\t/home/dell/coding/mcp/venv/bin/python /home/dell/coding/mcp/msfconsole/register_resources.py")
    else:
        print("Failed to register prompts and resources")
    
    return server


def main():
    """Main entry point"""
    # Create the server with prompts and resources
    server = create_dynamic_mcp()
    
    # The server needs to be run separately to avoid asyncio errors
    print("\nTo run the server:")
    print("\t/home/dell/coding/mcp/venv/bin/python -c \"from mcp.server.fastmcp import FastMCP; FastMCP('MSFConsole').run()\"")


if __name__ == "__main__":
    # Just run the main function
    main()

