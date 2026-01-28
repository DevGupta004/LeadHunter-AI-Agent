#!/bin/bash

# LeadHunter AI Agent - One-Command Installer
# Works on macOS and Linux (Ubuntu/Debian)

set -e

echo "🚀 LeadHunter AI Agent - Installation"
echo "========================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${BLUE}📋 Detected OS: ${MACHINE}${NC}"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    echo ""
    echo "Please install Python 3.8+ first:"
    if [ "$MACHINE" = "Mac" ]; then
        echo "  brew install python@3.12"
        echo "  Or download from: https://www.python.org/downloads/"
    else
        echo "  sudo apt-get update"
        echo "  sudo apt-get install python3 python3-pip python3-venv"
    fi
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ ${PYTHON_VERSION} found${NC}"

# Check Python version (3.8+)
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}❌ Python 3.8+ required. Found: ${PYTHON_VERSION}${NC}"
    exit 1
fi

# Check if we're in the project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${YELLOW}⚠️  Warning: requirements.txt not found${NC}"
    echo "Make sure you're in the LeadHunter-AI-Agent directory"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo ""
    echo -e "${BLUE}📦 Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade pip
echo ""
echo -e "${BLUE}⬆️  Upgrading pip...${NC}"
pip install --upgrade pip --quiet

# Install dependencies
echo ""
echo -e "${BLUE}📥 Installing Python dependencies...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Install Playwright browsers
echo ""
echo -e "${BLUE}🌐 Installing Playwright browsers...${NC}"
echo -e "${YELLOW}   This may take a few minutes (downloading ~250MB)...${NC}"
python3 -m playwright install chromium
echo -e "${GREEN}✅ Playwright browsers installed${NC}"

# Verify installation
echo ""
echo -e "${BLUE}🔍 Verifying installation...${NC}"
python3 -c "import playwright; import streamlit; import pandas; import openpyxl; print('✅ All modules imported successfully')" 2>/dev/null || {
    echo -e "${RED}❌ Verification failed${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Installation completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the scraper:"
echo "   streamlit run lead_hunter.py"
echo ""
echo "3. Open your browser to: http://localhost:8501"
echo ""
echo "For AI version, see README.md"
echo ""
