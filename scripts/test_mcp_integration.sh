#!/bin/bash
# scripts/test_mcp_integration.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing MCP Integration...${NC}"

# Check if mcp_client.py is being properly imported
echo -e "${YELLOW}Running basic test with mcp_client.py...${NC}"
python -c "from src.data_retrieval.mcp_client import MCPClient; client = MCPClient(); print('MCPClient imported successfully')"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to import MCPClient. Check your project structure.${NC}"
    exit 1
fi

# Run a simple search test using the client
echo -e "${YELLOW}Running a test search...${NC}"
cd mcp-service
python server.py --query "deep learning" --max_results 2 > test_results.json

if [ $? -ne 0 ]; then
    echo -e "${RED}Server test failed.${NC}"
    exit 1
fi

echo -e "${GREEN}Server test successful.${NC}"
echo -e "${YELLOW}Results saved to mcp-service/test_results.json${NC}"
echo -e "${GREEN}MCP integration test completed successfully.${NC}"