#!/usr/bin/env python3

"""
Documentation Tools for MSFConsole MCP
Provides functions to integrate and browse documentation
"""

import os
import logging

logger = logging.getLogger(__name__)

# Documentation directory path
DOCS_PATH = "/home/dell/coding/documentation/msfconsole/"

def list_available_docs():
    """
    List all available documentation files in the docs directory
    
    Returns:
        str: Formatted markdown list of available documentation
    """
    try:
        docs = os.listdir(DOCS_PATH)
        # Filter for markdown files
        docs = [doc for doc in docs if doc.endswith(".md")]
        
        if not docs:
            return "No documentation files found."
            
        # Sort alphabetically
        docs.sort()
        
        # Generate a formatted list with descriptions where possible
        output = "# Available Documentation\n\n"
        for doc in docs:
            doc_path = os.path.join(DOCS_PATH, doc)
            title = doc.replace(".md", "").replace("_", " ").title()
            
            # Try to extract first paragraph for description
            try:
                with open(doc_path, 'r') as f:
                    content = f.read(500)  # Read first 500 chars
                    # Try to extract first paragraph or header
                    header = None
                    for line in content.split('\n'):
                        if line.startswith('#'):
                            header = line.lstrip('#').strip()
                            break
                            
                    if header:
                        output += f"- **{title}** - {header}\n"
                    else:
                        output += f"- **{title}**\n"
            except Exception as e:
                logger.warning(f"Error reading doc header for {doc}: {e}")
                output += f"- **{title}**\n"
                
        return output
    except Exception as e:
        logger.error(f"Error listing documentation: {e}")
        return f"Error listing documentation: {str(e)}"

def get_document_content(document_name):
    """
    Get the content of a specific documentation file
    
    Args:
        document_name (str): Name of the document to retrieve
        
    Returns:
        str: Content of the document
    """
    try:
        # Handle different ways of specifying the document
        if not document_name.endswith(".md"):
            document_name += ".md"
            
        # For ease of use, convert spaces to underscores and lowercase
        doc_filename = document_name.lower().replace(" ", "_")
        
        doc_path = os.path.join(DOCS_PATH, doc_filename)
        
        # Check if the file exists
        if not os.path.exists(doc_path):
            # Try to find a close match
            docs = os.listdir(DOCS_PATH)
            docs = [doc for doc in docs if doc.endswith(".md")]
            
            # Try partial matching
            matches = [doc for doc in docs if doc_filename.replace(".md", "") in doc.lower()]
            
            if matches:
                if len(matches) == 1:
                    doc_path = os.path.join(DOCS_PATH, matches[0])
                else:
                    return f"Multiple matching documents found: {', '.join(matches)}\nPlease specify which one you want."
            else:
                return f"Document '{document_name}' not found."
        
        # Read the document
        with open(doc_path, 'r') as f:
            content = f.read()
            
        return content
    except Exception as e:
        logger.error(f"Error reading documentation: {e}")
        return f"Error reading documentation: {str(e)}"

def list_commands():
    """
    List all available commands in the MCP
    
    Returns:
        str: Formatted markdown list of commands with descriptions
    """
    commands = [
        {"name": "get_msf_version", "description": "Get the installed Metasploit Framework version"},
        {"name": "run_msf_command", "description": "Execute a command in msfconsole"},
        {"name": "search_modules", "description": "Search for modules in the Metasploit Framework"},
        {"name": "manage_workspaces", "description": "List and manage Metasploit workspaces"},
        {"name": "run_scan", "description": "Run a scan against target hosts"},
        {"name": "manage_database", "description": "Manage the Metasploit database"},
        {"name": "manage_sessions", "description": "List and manage Metasploit sessions"},
        {"name": "generate_payload", "description": "Generate a payload using msfvenom"},
        {"name": "show_module_info", "description": "Show detailed information about a Metasploit module"},
        {"name": "browse_documentation", "description": "Browse and view documentation files"},
        {"name": "list_commands", "description": "List all available commands and tools"}
    ]
    
    output = "# Available Commands\n\n"
    
    for cmd in commands:
        output += f"## {cmd['name']}\n"
        output += f"{cmd['description']}\n\n"
    
    # Add examples
    output += "\n# Usage Examples\n\n"
    output += "- `get_msf_version` - Check the installed Metasploit version\n"
    output += "- `run_msf_command command=\"help\"` - Run the help command in msfconsole\n"
    output += "- `search_modules query=\"windows\"` - Find modules related to Windows\n"
    output += "- `browse_documentation document_name=\"metasploit_cheatsheet\"` - View the Metasploit cheatsheet\n"
    
    return output
