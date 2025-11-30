#!/bin/bash
# scripts/start_mcp_server.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Store the original directory
ORIGINAL_DIR=$(pwd)

echo -e "${GREEN}Starting MCP Server...${NC}"

# Check if the mcp-service directory exists
if [ ! -d "mcp-service" ]; then
    echo -e "${RED}Error: mcp-service directory not found!${NC}"
    exit 1
fi

# Check if server.py exists
if [ ! -f "mcp-service/server.py" ]; then
    echo -e "${RED}Error: server.py not found in mcp-service directory!${NC}"
    exit 1
fi

# Create paper_cache directory if it doesn't exist
if [ ! -d "mcp-service/paper_cache" ]; then
    echo -e "${YELLOW}Creating paper_cache directory...${NC}"
    mkdir -p mcp-service/paper_cache
fi

# Make sure server.py is executable
chmod +x mcp-service/server.py

# Test the server first to make sure it's working
echo -e "${YELLOW}Testing server.py...${NC}"
cd mcp-service
python server.py --query "test" --max_results 1 > /dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Server test failed!${NC}"
    cd "$ORIGINAL_DIR"  # Return to original directory
    exit 1
fi

# Always return to the original directory
cd "$ORIGINAL_DIR"

# Start the server as FastMCP if possible
echo -e "${YELLOW}Starting MCP server...${NC}"
cd mcp-service
# Check if MCP package is installed
python -c "import mcp" 2>/dev/null
if [ $? -eq 0 ]; then
    # MCP is installed, run in FastMCP mode
    echo -e "${GREEN}Running in FastMCP mode...${NC}"
    python server.py
else
    # MCP not installed, run in standalone mode
    echo -e "${YELLOW}MCP package not installed. Running in standalone mode only.${NC}"
    echo -e "${YELLOW}Server is ready to receive queries.${NC}"
    echo -e "${YELLOW}Example: python server.py --query \"quantum computing\" --max_results 5${NC}"
    
    # Keep the server running in standalone mode
    # Run a simple loop that waits for user input to exit
    echo -e "${YELLOW}Press Ctrl+C to stop the server...${NC}"
    while true; do
        sleep 1
    done
fi