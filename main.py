#!/usr/bin/env python3
"""
Chess Teacher - Main Application Entry Point
"""

import sys
import os
import logging
from datetime import datetime

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def setup_logging():
    """Setup logging configuration for the application."""
    # Create logs directory if it doesn't exist
    logs_dir = os.path.join(project_root, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Configure logging
    log_file = os.path.join(logs_dir, f'chess_teacher_{datetime.now().strftime("%Y%m%d")}.log')
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

def check_dependencies():
    """Check if required dependencies are available."""
    logger = logging.getLogger(__name__)
    
    # Check for tkinter
    try:
        import tkinter
        logger.info("✅ Tkinter is available")
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
    required_packages = ['chess', 'requests', 'PIL']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"\nTo install: pip install {' '.join(missing_packages)}")
        sys.exit(1)

def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    logger = logging.getLogger(__name__)
    
    try:
        from data.database import create_connection, create_tables
        from config.settings import DATABASE_PATH
        
        # Create database connection
        conn = create_connection(DATABASE_PATH)
        if conn is None:
            logger.error("Failed to create database connection")
            return False
        
        # Create tables
        create_tables(conn)
        conn.close()
        
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False

def check_stockfish():
    """Check if Stockfish is available."""
    logger = logging.getLogger(__name__)
    
    try:
        from analysis.stockfish_analyzer import StockfishAnalyzer
        
        # Try to create a Stockfish analyzer instance
        analyzer = StockfishAnalyzer()
        logger.info("✅ Stockfish is available")
        return True
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Stockfish: {e}")
        return False

def main():
    """Main application entry point."""
    print("Chess Teacher - Starting...")
    
    # Setup logging first
    logger = setup_logging()
    logger.info("Starting Chess Teacher application")
    
    # Check dependencies
    logger.info("Checking dependencies...")
    check_dependencies()
    
    # Initialize database
    logger.info("Initializing database...")
    if not initialize_database():
        logger.error("Failed to initialize database")
        sys.exit(1)
    
    # Check Stockfish availability
    logger.info("Checking Stockfish availability...")
    stockfish_available = check_stockfish()
    
    # Import GUI components (only after all checks pass)
    try:
        from gui.main_window import MainWindow
        logger.info("✅ GUI components imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import GUI components: {e}")
        sys.exit(1)
    
    print("✅ All checks passed!")
    print("   Starting main application window...")
    logger.info("Creating main application window")
    
    # Create and run the main application
    try:
        app = MainWindow()
        app.run()
        logger.info("Application closed successfully")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()