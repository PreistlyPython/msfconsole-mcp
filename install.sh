#!/bin/bash

# MSFConsole MCP Installation Script
# This script installs all dependencies required for the MSFConsole MCP

echo "===== Installing MSFConsole MCP Dependencies ====="
echo

# Function to check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if Python 3 is installed
if ! command_exists python3; then
  echo "Error: Python 3 is required but not installed."
  echo "Please install Python 3 and try again."
  exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d " " -f 2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

echo "Detected Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
  echo "Warning: Python 3.8 or higher is recommended."
  read -p "Continue anyway? (y/n) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Check if pip is installed
if ! command_exists pip3; then
  echo "Installing pip for Python 3..."
  sudo apt-get update
  sudo apt-get install -y python3-pip
fi

# Check if Metasploit is installed
if ! command_exists msfconsole; then
  echo "Warning: Metasploit Framework (msfconsole) not found."
  echo "The MCP requires Metasploit Framework to be installed."
  echo
  read -p "Would you like to install Metasploit Framework now? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing Metasploit Framework..."
    curl https://raw.githubusercontent.com/rapid7/metasploit-omnibus/master/config/templates/metasploit-framework-wrappers/msfupdate.erb > msfinstall
    chmod +x msfinstall
    sudo ./msfinstall
    rm msfinstall
  else
    echo "Please install Metasploit Framework manually and run this script again."
    echo "You can find installation instructions at: https://docs.metasploit.com/docs/using-metasploit/getting-started/installation.html"
    echo
    read -p "Continue with the rest of the installation? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
fi

# Install python dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

# Install MCP SDK
echo "Installing MCP SDK..."
pip3 install mcp[cli]

# Create config directory if it doesn't exist
mkdir -p ~/.config/mcp

echo
echo "===== Installation Complete ====="
echo
echo "You can now start the MSF Console MCP server with:"
echo "./start_mcp.sh"
echo
echo "If you encounter any issues, please check the documentation or create an issue on GitHub."
