# LeadHunter AI Agent - Windows PowerShell Installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "🚀 LeadHunter AI Agent - Installation" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion found" -ForegroundColor Green
} catch {
    Write-Host "❌ Python is not installed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.8+ from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Make sure to check 'Add Python to PATH' during installation" -ForegroundColor Yellow
    exit 1
}

# Check Python version
$pythonMajor = python -c "import sys; print(sys.version_info.major)" 2>&1
$pythonMinor = python -c "import sys; print(sys.version_info.minor)" 2>&1

if ([int]$pythonMajor -lt 3 -or ([int]$pythonMajor -eq 3 -and [int]$pythonMinor -lt 8)) {
    Write-Host "❌ Python 3.8+ required. Found: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Check if we're in the project directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "⚠️  Warning: requirements.txt not found" -ForegroundColor Yellow
    Write-Host "Make sure you're in the LeadHunter-AI-Agent directory" -ForegroundColor Yellow
    $response = Read-Host "Continue anyway? (y/n)"
    if ($response -ne "y" -and $response -ne "Y") {
        exit 1
    }
}

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host ""
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Blue
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Blue
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host ""
Write-Host "⬆️  Upgrading pip..." -ForegroundColor Blue
python -m pip install --upgrade pip --quiet

# Install dependencies
Write-Host ""
Write-Host "📥 Installing Python dependencies..." -ForegroundColor Blue
pip install -r requirements.txt --quiet
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Install Playwright browsers
Write-Host ""
Write-Host "🌐 Installing Playwright browsers..." -ForegroundColor Blue
Write-Host "   This may take a few minutes (downloading ~250MB)..." -ForegroundColor Yellow
python -m playwright install chromium
Write-Host "✅ Playwright browsers installed" -ForegroundColor Green

# Verify installation
Write-Host ""
Write-Host "🔍 Verifying installation..." -ForegroundColor Blue
try {
    python -c "import playwright; import streamlit; import pandas; import openpyxl; print('✅ All modules imported successfully')" 2>&1 | Out-Null
    Write-Host "✅ Verification successful" -ForegroundColor Green
} catch {
    Write-Host "❌ Verification failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Installation completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Activate virtual environment:"
Write-Host "   venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "2. Run the scraper:"
Write-Host "   streamlit run lead_hunter.py"
Write-Host ""
Write-Host "3. Open your browser to: http://localhost:8501"
Write-Host ""
Write-Host "For AI version, see README.md"
Write-Host ""
