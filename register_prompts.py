#!/usr/bin/env python3

"""
Script to register Metasploit MCP prompts with the MCP Inspector
"""

import os
import json
import argparse
import requests

def register_prompts(mcp_url, prompts_file):
    """Register prompts with the MCP Inspector."""
    try:
        # Load prompts from JSON file
        with open(prompts_file, 'r') as f:
            data = json.load(f)
            prompts = data.get('prompts', [])
            
        if not prompts:
            print("No prompts found in the JSON file.")
            return False
        
        # Register each prompt with the MCP Inspector
        for prompt in prompts:
            title = prompt.get('title', 'Untitled')
            description = prompt.get('description', '')
            text = prompt.get('text', '')
            
            print(f"Registering prompt: {title}")
            
            # Create the prompt using the MCP Inspector API
            payload = {
                'title': title,
                'description': description,
                'text': text
            }
            
            response = requests.post(f"{mcp_url}/api/prompts", json=payload)
            if response.status_code == 200 or response.status_code == 201:
                print(f"Successfully registered prompt: {title}")
            else:
                print(f"Failed to register prompt: {title}")
                print(f"Status code: {response.status_code}")
                print(f"Response: {response.text}")
                
        return True
    
    except Exception as e:
        print(f"Error registering prompts: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Register MCP prompts')
    parser.add_argument('--url', default='http://localhost:8000', help='MCP Inspector URL')
    parser.add_argument('--prompts', default='prompts.json', help='Path to prompts JSON file')
    
    args = parser.parse_args()
    
    success = register_prompts(args.url, args.prompts)
    
    if success:
        print("Prompts registration completed.")
    else:
        print("Failed to register prompts.")

if __name__ == "__main__":
    main()
