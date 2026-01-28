#!/bin/bash

# LeadHunter AI Agent - Setup Script
# This script sets up the project on any laptop

set -e  # Exit on error

echo "🚀 LeadHunter AI Agent - Setup"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo "📋 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    echo "Please install Python 3.8+ first:"
    echo "  macOS: brew install python@3.12"
    echo "  Linux: sudo apt-get install python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip --quiet

# Install Python dependencies
echo ""
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt --quiet
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Install Playwright browsers
echo ""
echo "🌐 Installing Playwright browsers..."
echo "   This may take a few minutes..."
python3 -m playwright install chromium
echo -e "${GREEN}✅ Playwright browsers installed${NC}"

# Verify installation
echo ""
echo "🔍 Verifying installation..."
python3 -c "import playwright; print('✅ Playwright imported successfully')" 2>/dev/null || {
    echo -e "${RED}❌ Playwright verification failed${NC}"
    exit 1
}

python3 -c "import streamlit; print('✅ Streamlit imported successfully')" 2>/dev/null || {
    echo -e "${RED}❌ Streamlit verification failed${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ Setup completed successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Run the simple scraper:"
echo "   source venv/bin/activate"
echo "   streamlit run lead_hunter.py"
echo ""
echo "2. Or run the AI-powered scraper:"
echo "   # First, start Ollama in another terminal:"
echo "   ollama serve"
echo ""
echo "   # Then run:"
echo "   source venv/bin/activate"
echo "   streamlit run lead_hunter_ai.py"
echo ""
echo "3. Open your browser to: http://localhost:8501"
echo ""
