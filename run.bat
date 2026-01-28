@echo off
REM LeadHunter AI Agent - Windows Quick Run Script
REM Usage: run.bat [simple|ai]

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo ❌ Virtual environment not found!
    echo.
    echo Please run setup first:
    echo   python setup.py
    echo   or
    echo   powershell -ExecutionPolicy Bypass -File install.ps1
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Determine which script to run
if "%1"=="ai" (
    echo 🤖 Starting AI-Powered Scraper...
    echo ⚠️  Make sure Ollama is running: ollama serve
    echo.
    streamlit run lead_hunter_ai.py
) else (
    echo ⚡ Starting Simple Scraper...
    echo.
    streamlit run lead_hunter.py
)
