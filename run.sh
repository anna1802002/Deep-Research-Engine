#!/bin/bash

# Run Deep Research Engine Demo
# This script runs the API key check and then the demo

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deep Research Engine Demo${NC}"
echo -e "${YELLOW}Checking dependencies...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Try to run API key check
echo -e "${YELLOW}Checking API keys...${NC}"
python3 check_api_keys.py

# Check if API key check was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: API key check failed. Please configure your API keys before running the demo.${NC}"
    echo -e "${YELLOW}See config/api_keys.sample.yaml for required keys.${NC}"
    exit 1
fi

# Run the demo
echo -e "${GREEN}Running Deep Research Engine demo...${NC}"
python3 demo.py

# Check if demo was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Demo failed to run correctly.${NC}"
    exit 1
else
    echo -e "${GREEN}Demo completed successfully!${NC}"
fi