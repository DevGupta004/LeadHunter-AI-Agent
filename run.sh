#!/bin/bash

# LeadHunter AI Agent - Quick Run Script
# Usage: ./run.sh [simple|ai]

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo ""
    echo "Please run setup first:"
    echo "  ./install.sh"
    echo "  or"
    echo "  python3 setup.py"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Determine which script to run
SCRIPT_TYPE=${1:-simple}

if [ "$SCRIPT_TYPE" = "ai" ]; then
    echo -e "${BLUE}🤖 Starting AI-Powered Scraper...${NC}"
    echo -e "${YELLOW}⚠️  Make sure Ollama is running: ollama serve${NC}"
    echo ""
    streamlit run lead_hunter_ai.py
else
    echo -e "${BLUE}⚡ Starting Simple Scraper...${NC}"
    echo ""
    streamlit run lead_hunter.py
fi
