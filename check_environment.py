#!/usr/bin/env python3
"""
Environment check script for Chess Teacher application.
Verifies that all required system dependencies are available.
"""

import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is sufficient."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ is required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def check_tkinter():
    """Check if tkinter is available."""
    try:
        import tkinter
        print("✅ Tkinter - OK")
        return True
    except ImportError as e:
        print("❌ Tkinter not available")
        print("   This is required for the GUI.")
        print("\n   To install tkinter:")
        
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print("   macOS (Homebrew): brew install python-tk@3.12")
        elif system == "linux":
            print("   Ubuntu/Debian: sudo apt-get install python3-tk")
            print("   CentOS/RHEL: sudo yum install python3-tkinter")
        elif system == "windows":
            print("   Windows: Tkinter should be included with Python from python.org")
            print("   If missing, reinstall Python and ensure 'tcl/tk and IDLE' is selected")
        
        print(f"\n   Error details: {e}")
        return False

def check_stockfish():
    """Check if Stockfish is available in PATH."""
    try:
        result = subprocess.run(['stockfish', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Stockfish - OK")
            return True
        else:
            print("❌ Stockfish not working properly")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Stockfish not found in PATH")
        print("   This is required for chess analysis.")
        print("\n   To install Stockfish:")
        
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print("   macOS: brew install stockfish")
        elif system == "linux":
            print("   Ubuntu/Debian: sudo apt-get install stockfish")
            print("   CentOS/RHEL: sudo yum install stockfish")
        elif system == "windows":
            print("   Windows: Download from https://stockfishchess.org/download/")
            print("   Add stockfish.exe to your PATH or place it in the project directory")
        
        return False

def check_python_packages():
    """Check if required Python packages are installed."""
    required_packages = [
        'chess',
        'requests', 
        'PIL',  # pillow is imported as PIL
        'stockfish'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - OK")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n   To install missing packages:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def main():
    """Run all environment checks."""
    print("Chess Teacher - Environment Check")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_tkinter,
        check_stockfish,
        check_python_packages
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All checks passed! You're ready to run Chess Teacher.")
        print("\n   To start the application:")
        print("   python main.py")
    else:
        print("❌ Some checks failed. Please install the missing dependencies.")
        print("   See the README.md file for detailed installation instructions.")
        sys.exit(1)

if __name__ == "__main__":
    main() 