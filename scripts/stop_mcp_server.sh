#!/bin/bash
# scripts/stop_mcp_server.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping MCP Server...${NC}"

# Check if PID file exists
if [ -f "mcp-service/server.pid" ]; then
    SERVER_PID=$(cat mcp-service/server.pid)
    
    # Check if process is running
    if ps -p $SERVER_PID > /dev/null; then
        echo -e "${YELLOW}Stopping MCP server with PID: $SERVER_PID${NC}"
        kill $SERVER_PID
        
        # Wait for process to stop
        for i in {1..5}; do
            if ! ps -p $SERVER_PID > /dev/null; then
                echo -e "${GREEN}MCP server stopped successfully${NC}"
                rm mcp-service/server.pid
                exit 0
            fi
            echo "Waiting for server to stop..."
            sleep 1
        done
        
        # Force kill if needed
        echo -e "${YELLOW}Server still running. Forcing termination...${NC}"
        kill -9 $SERVER_PID
        rm mcp-service/server.pid
        echo -e "${GREEN}MCP server forcefully terminated${NC}"
    else
        echo -e "${YELLOW}MCP server not running (PID: $SERVER_PID)${NC}"
        rm mcp-service/server.pid
    fi
else
    echo -e "${YELLOW}No PID file found. Looking for any running server processes...${NC}"
    
    # Try to find any running server processes
    SERVER_PIDS=$(pgrep -f "python.*server.py")
    
    if [ -n "$SERVER_PIDS" ]; then
        echo -e "${YELLOW}Found server processes: $SERVER_PIDS${NC}"
        for pid in $SERVER_PIDS; do
            echo -e "${YELLOW}Stopping process: $pid${NC}"
            kill $pid
        done
        echo -e "${GREEN}Server processes stopped${NC}"
    else
        echo -e "${RED}No running MCP server processes found${NC}"
    fi
fi