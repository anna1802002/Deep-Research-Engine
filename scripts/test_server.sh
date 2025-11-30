#!/bin/bash
# scripts/test_server.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing MCP Server...${NC}"

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

# Make server.py executable
chmod +x mcp-service/server.py

# Test server.py directly with a simple query
echo -e "${YELLOW}Testing direct execution mode...${NC}"
cd mcp-service
python server.py --query "protein folding" --max_results 2

echo -e "${GREEN}Server test completed.${NC}"