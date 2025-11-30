#!/bin/bash
# scripts/test_mcp_server.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing MCP Server...${NC}"

# Check if server is running
if [ -f "mcp-service/server.pid" ]; then
    SERVER_PID=$(cat mcp-service/server.pid)
    if ! ps -p $SERVER_PID > /dev/null; then
        echo -e "${RED}Server not running! PID file exists but process is dead.${NC}"
        echo -e "${YELLOW}Start the server with: ./scripts/start_mcp_server.sh${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}No server PID file found. Checking for running processes...${NC}"
    SERVER_PIDS=$(pgrep -f "python.*server.py")
    
    if [ -z "$SERVER_PIDS" ]; then
        echo -e "${RED}Server not running! Start it with: ./scripts/start_mcp_server.sh${NC}"
        exit 1
    fi
fi

# Test server with a simple query
echo -e "${YELLOW}Testing server with a simple query...${NC}"
cd mcp-service
QUERY_RESULT=$(python server.py --query "quantum computing" --max_results 2)

# Check if we got a valid response
if [[ $QUERY_RESULT == *"title"* && $QUERY_RESULT == *"abstract"* ]]; then
    echo -e "${GREEN}Server test successful!${NC}"
    echo -e "${YELLOW}Response preview:${NC}"
    echo "$QUERY_RESULT" | head -n 10
    echo "..."
    exit 0
else
    echo -e "${RED}Server test failed!${NC}"
    echo -e "${YELLOW}Response:${NC}"
    echo "$QUERY_RESULT"
    exit 1
fi