#!/usr/bin/env python3

"""
Run a standalone MCP server with the prompts and resources
"""

import os
import sys
import json
from mcp.server.fastmcp import FastMCP

# First register the prompts and resources
script_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(script_dir, "mcp_config.json")

# Initialize server
server = FastMCP(name="MSFConsole Resources", version="0.1.0")

try:
    # Load config
    with open(config_path, "r") as f:
        config = json.load(f)
        
    # Register prompts
    for prompt_data in config.get("prompts", []):
        name = prompt_data.get("title")
        description = prompt_data.get("description")
        content = prompt_data.get("content")
        
        # Create a unique function for each prompt
        def create_prompt_fn(prompt_content):
            @server.prompt(name=name, description=description)
            def prompt_fn():
                return [{"role": "user", "content": prompt_content}]
            return prompt_fn
            
        create_prompt_fn(content)
        print(f"Registered prompt: {name}")
        
    # Register resources  
    for resource_data in config.get("resources", []):
        name = resource_data.get("title")
        description = resource_data.get("description")
        content = resource_data.get("content")
        
        # Convert name to URI format
        uri = f"resource://{name.lower().replace(' ', '-')}"
        
        # Create a unique function for each resource
        def create_resource_fn(resource_content):
            @server.resource(uri=uri, name=name, description=description)
            def resource_fn():
                return resource_content
            return resource_fn
            
        create_resource_fn(content)
        print(f"Registered resource: {name} at {uri}")
        
    print("All prompts and resources registered successfully")
    
except Exception as e:
    print(f"Error setting up server: {e}")
    sys.exit(1)

# Run the server
print("\nStarting MCP Resource Server...")
server.run()
