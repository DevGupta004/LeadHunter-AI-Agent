#!/usr/bin/env python3
"""
LeadHunter AI Agent - Cross-platform Setup Script
This script sets up the project on any laptop (Windows, macOS, Linux)
"""

import sys
import subprocess
import os
import platform
from pathlib import Path

def print_colored(text, color='green'):
    """Print colored text"""
    colors = {
        'green': '\033[0;32m',
        'yellow': '\033[1;33m',
        'red': '\033[0;31m',
        'blue': '\033[0;34m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['reset']}")

def run_command(cmd, check=True, shell=False):
    """Run a command and return success status"""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        result = subprocess.run(
            cmd,
            check=check,
            shell=shell,
            capture_output=True,
            text=True
        )
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr

def check_python():
    """Check if Python 3.8+ is installed"""
    print_colored("📋 Checking Python version...", 'blue')
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_colored(f"❌ Python 3.8+ required. Found: {version.major}.{version.minor}", 'red')
        return False
    
    print_colored(f"✅ Python {version.major}.{version.minor}.{version.micro} found", 'green')
    return True

def create_venv():
    """Create virtual environment if it doesn't exist"""
    venv_path = Path('venv')
    
    if venv_path.exists():
        print_colored("✅ Virtual environment already exists", 'green')
        return True
    
    print_colored("📦 Creating virtual environment...", 'blue')
    success, output = run_command([sys.executable, '-m', 'venv', 'venv'])
    
    if success:
        print_colored("✅ Virtual environment created", 'green')
        return True
    else:
        print_colored(f"❌ Failed to create virtual environment: {output}", 'red')
        return False

def get_pip_command():
    """Get the pip command for the virtual environment"""
    system = platform.system()
    if system == 'Windows':
        return 'venv\\Scripts\\pip.exe'
    else:
        return 'venv/bin/pip'

def get_python_command():
    """Get the python command for the virtual environment"""
    system = platform.system()
    if system == 'Windows':
        return 'venv\\Scripts\\python.exe'
    else:
        return 'venv/bin/python'

def install_dependencies():
    """Install Python dependencies"""
    print_colored("⬆️  Upgrading pip...", 'blue')
    pip_cmd = get_pip_command()
    run_command([pip_cmd, 'install', '--upgrade', 'pip'], check=False)
    
    print_colored("📥 Installing Python dependencies...", 'blue')
    print_colored("   This may take a few minutes...", 'yellow')
    
    # Check if requirements.txt exists
    if not Path('requirements.txt').exists():
        print_colored("❌ requirements.txt not found!", 'red')
        print_colored("   Make sure you're in the LeadHunter-AI-Agent directory", 'yellow')
        return False
    
    success, output = run_command([pip_cmd, 'install', '-r', 'requirements.txt'])
    
    if success:
        print_colored("✅ Dependencies installed", 'green')
        return True
    else:
        print_colored(f"❌ Failed to install dependencies: {output}", 'red')
        print_colored("   Try running: pip install -r requirements.txt manually", 'yellow')
        return False

def install_playwright_browsers():
    """Install Playwright browsers"""
    print_colored("🌐 Installing Playwright browsers...", 'blue')
    print_colored("   This may take a few minutes (downloading ~250MB)...", 'yellow')
    
    python_cmd = get_python_command()
    success, output = run_command([python_cmd, '-m', 'playwright', 'install', 'chromium'])
    
    if success:
        print_colored("✅ Playwright browsers installed", 'green')
        return True
    else:
        print_colored(f"❌ Failed to install Playwright browsers: {output}", 'red')
        print_colored("   Try running: python -m playwright install chromium manually", 'yellow')
        print_colored("   On Linux, you may need to install system dependencies first", 'yellow')
        return False

def verify_installation():
    """Verify that everything is installed correctly"""
    print_colored("🔍 Verifying installation...", 'blue')
    
    python_cmd = get_python_command()
    all_checks_passed = True
    
    # Check Playwright
    success, _ = run_command([python_cmd, '-c', 'import playwright'], check=False)
    if not success:
        print_colored("❌ Playwright verification failed", 'red')
        all_checks_passed = False
    else:
        print_colored("✅ Playwright imported successfully", 'green')
    
    # Check Streamlit
    success, _ = run_command([python_cmd, '-c', 'import streamlit'], check=False)
    if not success:
        print_colored("❌ Streamlit verification failed", 'red')
        all_checks_passed = False
    else:
        print_colored("✅ Streamlit imported successfully", 'green')
    
    # Check pandas
    success, _ = run_command([python_cmd, '-c', 'import pandas'], check=False)
    if not success:
        print_colored("❌ Pandas verification failed", 'red')
        all_checks_passed = False
    else:
        print_colored("✅ Pandas imported successfully", 'green')
    
    # Check openpyxl
    success, _ = run_command([python_cmd, '-c', 'import openpyxl'], check=False)
    if not success:
        print_colored("❌ OpenPyXL verification failed", 'red')
        all_checks_passed = False
    else:
        print_colored("✅ OpenPyXL imported successfully", 'green')
    
    return all_checks_passed

def print_next_steps():
    """Print next steps for the user"""
    system = platform.system()
    
    if system == 'Windows':
        activate_cmd = 'venv\\Scripts\\activate'
    else:
        activate_cmd = 'source venv/bin/activate'
    
    print_colored("\n================================\n✅ Setup completed successfully!\n================================", 'green')
    print("\n📝 Next steps:\n")
    print("1. Activate virtual environment:")
    print(f"   {activate_cmd}\n")
    print("2. Run the simple scraper:")
    print("   streamlit run lead_hunter.py\n")
    print("3. Or run the AI-powered scraper:")
    print("   # First, start Ollama in another terminal:")
    print("   ollama serve")
    print("   # Then run:")
    print("   streamlit run lead_hunter_ai.py\n")
    print("4. Open your browser to: http://localhost:8501\n")

def main():
    """Main setup function"""
    print_colored("🚀 LeadHunter AI Agent - Setup", 'blue')
    print_colored("================================", 'blue')
    print()
    
    # Check Python
    if not check_python():
        sys.exit(1)
    
    # Create virtual environment
    if not create_venv():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Install Playwright browsers
    if not install_playwright_browsers():
        sys.exit(1)
    
    # Verify installation
    if not verify_installation():
        sys.exit(1)
    
    # Print next steps
    print_next_steps()

if __name__ == '__main__':
    main()
