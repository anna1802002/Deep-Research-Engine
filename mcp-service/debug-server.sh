#!/bin/bash
# Debug MCP server startup

# Color codes for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting MCP Server with Debug Mode...${NC}"

# Check Python environment
echo -e "${YELLOW}Python Version:${NC}"
python --version

# Check for mcp package
echo -e "${YELLOW}Checking for MCP package:${NC}"
pip list | grep mcp

# Check if server.py exists in current directory
if [ -f "server.py" ]; then
    echo -e "${GREEN}Found server.py${NC}"
    
    # Display first few lines to confirm it's the correct file
    echo -e "${YELLOW}First 10 lines of server.py:${NC}"
    head -n 10 server.py
    
    # Run the server with error output captured
    echo -e "${YELLOW}Running Python command: python server.py${NC}"
    echo -e "${YELLOW}If the server doesn't start properly, check the error output below:${NC}"
    python server.py 2>&1
elif [ -f "paste.txt" ]; then
    # If server.py doesn't exist but paste.txt does, create server.py from paste.txt
    echo -e "${YELLOW}Creating server.py from paste.txt...${NC}"
    cp paste.txt server.py
    echo -e "${GREEN}Created server.py${NC}"
    
    # Display first few lines to confirm it's the correct file
    echo -e "${YELLOW}First 10 lines of server.py:${NC}"
    head -n 10 server.py
    
    # Run the server with error output captured
    echo -e "${YELLOW}Running Python command: python server.py${NC}"
    echo -e "${YELLOW}If the server doesn't start properly, check the error output below:${NC}"
    python server.py 2>&1
else
    echo -e "${RED}Error: Neither server.py nor paste.txt found in current directory!${NC}"
    echo -e "${YELLOW}Current directory contains:${NC}"
    ls -la
    exit 1
fi

echo -e "${RED}MCP server has stopped.${NC}"