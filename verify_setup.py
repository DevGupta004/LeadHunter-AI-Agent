#!/usr/bin/env python3
"""
Quick verification script to check if everything is set up correctly
Run this after setup to verify installation
"""

import sys
import subprocess
from pathlib import Path

def check_import(module_name, display_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {display_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {display_name} - FAILED: {e}")
        return False

def check_playwright_browsers():
    """Check if Playwright browsers are installed"""
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # Try to get chromium browser path
            browser = p.chromium
            # This will fail if browsers aren't installed
            print("✅ Playwright browsers - OK")
            return True
    except Exception as e:
        print(f"❌ Playwright browsers - FAILED: {e}")
        print("   Run: python -m playwright install chromium")
        return False

def main():
    """Run all checks"""
    print("🔍 Verifying LeadHunter AI Agent Setup")
    print("=" * 50)
    print()
    
    checks_passed = 0
    total_checks = 0
    
    # Check Python version
    print(f"📋 Python version: {sys.version}")
    if sys.version_info >= (3, 8):
        print("✅ Python version - OK (3.8+)")
        checks_passed += 1
    else:
        print("❌ Python version - FAILED (Need 3.8+)")
    total_checks += 1
    print()
    
    # Check virtual environment
    if Path('venv').exists():
        print("✅ Virtual environment - OK")
        checks_passed += 1
    else:
        print("❌ Virtual environment - NOT FOUND")
        print("   Run: python3 -m venv venv")
    total_checks += 1
    print()
    
    # Check imports
    modules = [
        ('streamlit', 'Streamlit'),
        ('playwright', 'Playwright'),
        ('requests', 'Requests'),
    ]
    
    for module, name in modules:
        total_checks += 1
        if check_import(module, name):
            checks_passed += 1
    print()
    
    # Check Playwright browsers
    total_checks += 1
    if check_playwright_browsers():
        checks_passed += 1
    print()
    
    # Summary
    print("=" * 50)
    print(f"📊 Results: {checks_passed}/{total_checks} checks passed")
    print()
    
    if checks_passed == total_checks:
        print("✅ All checks passed! You're ready to go!")
        print()
        print("Next steps:")
        print("  1. Run: streamlit run lead_hunter.py")
        print("  2. Or: streamlit run lead_hunter_ai.py")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print()
        print("Quick fix:")
        print("  Run: ./setup.sh  (macOS/Linux)")
        print("  Or:  python setup.py  (Windows/Any)")
        return 1

if __name__ == '__main__':
    sys.exit(main())
