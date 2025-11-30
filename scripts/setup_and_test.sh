#!/bin/bash
# scripts/setup_and_test.sh

set -e

# Project root directory
PROJ_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJ_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deep Research Engine - Setup and Test Script${NC}\n"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Set up API keys
echo -e "\n${YELLOW}Setting up API keys...${NC}"
python scripts/setup_api_keys.py

# Verify API keys
echo -e "\n${YELLOW}Verifying API keys...${NC}"
API_KEYS_OK=$(python scripts/setup_api_keys.py --verify)

# Run tests
echo -e "\n${YELLOW}Running tests...${NC}"
if [ "$API_KEYS_OK" = "true" ]; then
    echo -e "${GREEN}Running tests with real API calls${NC}"
    python -m tests.run_tests
else
    echo -e "${YELLOW}Some API keys are missing. Running tests with mocks instead.${NC}"
    python -m tests.run_tests_mock
fi

echo -e "\n${GREEN}Setup and tests completed!${NC}"