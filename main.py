#!/usr/bin/env python3
"""
Chess Teacher - Main Application Entry Point
"""

import sys
import os

def check_dependencies():
    """Check if required dependencies are available."""
    # Check for tkinter
    try:
        import tkinter
    except ImportError:
        print("❌ Tkinter is not available!")
        print("\nTkinter is required for the GUI but is not included in your Python installation.")
        print("\nTo fix this:")
        
        import platform
        system = platform.system().lower()
        if system == "darwin":  # macOS
            print("  macOS (Homebrew): brew install python-tk@3.12")
        elif system == "linux":
            print("  Ubuntu/Debian: sudo apt-get install python3-tk")
            print("  CentOS/RHEL: sudo yum install python3-tkinter")
        elif system == "windows":
            print("  Windows: Reinstall Python from python.org and ensure 'tcl/tk and IDLE' is selected")
        
        print("\nAfter installing tkinter, restart your terminal and try again.")
        sys.exit(1)
    
    # Check for other required packages
    required_packages = ['chess', 'requests', 'pillow']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"\nTo install: pip install {' '.join(missing_packages)}")
        sys.exit(1)

def main():
    """Main application entry point."""
    print("Chess Teacher - Starting...")
    
    # Check dependencies first
    check_dependencies()
    
    # Import GUI components (only after tkinter check passes)
    try:
        from gui.main_window import MainWindow
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        sys.exit(1)
    
    print("✅ Dependencies check passed!")
    print("   Starting main application window...")
    
    # Create and run the main application
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()