#!/bin/bash
# run_demo.sh - Script to run the complete Deep Research Engine demo

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deep Research Engine - Complete Demo${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Ensure demo directory exists
if [ ! -d "demo" ]; then
    echo -e "${YELLOW}Creating demo directory...${NC}"
    mkdir -p demo
fi

# Create the modified demo script if it doesn't exist
if [ ! -f "demo/complete_demo.py" ]; then
    echo -e "${YELLOW}Setting up demo script...${NC}"
    
    # Copy the modified script
    if [ -f "modified-demo-script.py" ]; then
        cp modified-demo-script.py demo/complete_demo.py
        chmod +x demo/complete_demo.py
    else
        echo -e "${RED}Error: Modified demo script not found.${NC}"
        exit 1
    fi
fi

# Create necessary directories
echo -e "${YELLOW}Setting up environment...${NC}"
mkdir -p logs output visualizations

# Run the demo
echo -e "${YELLOW}Running Deep Research Engine demo...${NC}"
echo -e "${YELLOW}----------------------------------------${NC}"

# Get command line arguments
QUERY="$*"

if [ -z "$QUERY" ]; then 
    echo -e "${YELLOW}No query provided. Using default query.${NC}"
    python3 demo/complete_demo.py
else
    echo -e "${BLUE}Researching:${NC} ${QUERY}"
    python3 demo/complete_demo.py "$QUERY"
fi

# Check if demo was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Demo failed to run correctly.${NC}"
    exit 1
else
    echo -e "${GREEN}Demo completed successfully!${NC}"
    
    # Find the most recent output directory
    LATEST_OUTPUT=$(ls -td output/* | head -n 1)
    if [ -n "$LATEST_OUTPUT" ]; then
        echo -e "${YELLOW}Report generated at:${NC} ${LATEST_OUTPUT}/research_report.md"
    else
        echo -e "${YELLOW}Check the 'output' directory for the generated report.${NC}"
    fi
fi