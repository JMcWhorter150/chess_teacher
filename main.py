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
        from gui.chess_board import ChessBoardWidget
        import tkinter as tk
    except ImportError as e:
        print(f"❌ Failed to import GUI components: {e}")
        sys.exit(1)
    
    # Create main window
    root = tk.Tk()
    root.title("Chess Teacher")
    root.geometry("600x500")
    
    # Add a simple test to show the chess board works
    test_label = tk.Label(root, text="Chess Teacher - Section 5 Complete!", 
                         font=("Arial", 16))
    test_label.pack(pady=20)
    
    # Create and display chess board
    chess_board = ChessBoardWidget(root, size=400)
    chess_board.pack(pady=20)
    
    # Add status
    status_label = tk.Label(root, text="Click on pieces to make moves!", 
                           font=("Arial", 12))
    status_label.pack(pady=10)
    
    print("✅ Chess Teacher started successfully!")
    print("   GUI window should now be visible.")
    
    # Start the GUI event loop
    root.mainloop()

if __name__ == "__main__":
    main()