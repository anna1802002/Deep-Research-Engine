#!/bin/bash

# setup.sh - Initial setup script for Deep Research Engine

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Deep Research Engine - Setup Script${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed.${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}Error: Failed to create virtual environment.${NC}"
        exit 1
    fi
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Check if activation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to activate virtual environment.${NC}"
    exit 1
fi

# Install requirements
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to install dependencies.${NC}"
    exit 1
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs cache config

# Check if API keys file exists, if not create from sample
if [ ! -f "config/api_keys.yaml" ]; then
    echo -e "${YELLOW}Creating API keys configuration file...${NC}"
    if [ -f "config/api_keys.sample.yaml" ]; then
        cp config/api_keys.sample.yaml config/api_keys.yaml
        echo -e "${YELLOW}Please edit config/api_keys.yaml to add your API keys.${NC}"
    else
        echo -e "${RED}Error: api_keys.sample.yaml not found.${NC}"
        echo -e "${YELLOW}Creating empty API keys file...${NC}"
        touch config/api_keys.yaml
        echo "# Add your API keys here" > config/api_keys.yaml
        echo "GOOGLE_API_KEY: \"\"" >> config/api_keys.yaml
        echo "GOOGLE_CSE_ID: \"\"" >> config/api_keys.yaml
        echo "GOOGLE_SCHOLAR_API_KEY: \"\"" >> config/api_keys.yaml
        echo "GOOGLE_SCHOLAR_CX: \"\"" >> config/api_keys.yaml
        echo "OPENAI_API_KEY: \"\"" >> config/api_keys.yaml
        echo "GROQ_API_KEY: \"\"" >> config/api_keys.yaml
    fi
fi

# Create logging config if it doesn't exist
if [ ! -f "config/logging.yaml" ]; then
    echo -e "${YELLOW}Creating logging configuration...${NC}"
    cat > config/logging.yaml << EOF
version: 1
disable_existing_loggers: false

formatters:
  simple:
    format: "[%(asctime)s] %(levelname)s - %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: DEBUG
    formatter: simple
    stream: ext://sys.stdout

  file:
    class: logging.FileHandler
    level: INFO
    formatter: simple
    filename: logs/deep_research.log

loggers:
  deep_research:
    level: DEBUG
    handlers: [console, file]
    propagate: no
EOF
fi

# Make scripts executable
echo -e "${YELLOW}Making scripts executable...${NC}"
chmod +x run.sh setup.sh

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}To run the demo, execute: ./run.sh${NC}"
echo -e "${YELLOW}Make sure to add your API keys to config/api_keys.yaml${NC}"