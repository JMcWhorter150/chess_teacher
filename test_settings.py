#!/usr/bin/env python3
"""
Test script to verify database settings functionality
"""

import sys
import os

# Add project root to path for imports
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from data.database import create_connection, SettingsManager
from config.settings import DATABASE_PATH

def test_settings():
    """Test the settings functionality."""
    print("Testing database settings...")
    
    # Create database connection
    conn = create_connection(DATABASE_PATH)
    if not conn:
        print("❌ Could not connect to database")
        return False
    
    # Create tables first
    from data.database import create_tables
    create_tables(conn)
    
    # Create settings manager
    settings_manager = SettingsManager(conn)
    
    # Test setting and getting values
    print("\nTesting basic settings operations...")
    
    # Test username
    settings_manager.set_username("testuser")
    username = settings_manager.get_username()
    print(f"Username: {username}")
    assert username == "testuser", "Username not saved correctly"
    
    # Test blunder threshold
    settings_manager.set_blunder_threshold(250)
    threshold = settings_manager.get_blunder_threshold()
    print(f"Blunder threshold: {threshold}")
    assert threshold == 250, "Blunder threshold not saved correctly"
    
    # Test analysis depth
    settings_manager.set_analysis_depth(20)
    depth = settings_manager.get_analysis_depth()
    print(f"Analysis depth: {depth}")
    assert depth == 20, "Analysis depth not saved correctly"
    
    # Test max positions
    settings_manager.set_max_positions(15)
    max_pos = settings_manager.get_max_positions()
    print(f"Max positions: {max_pos}")
    assert max_pos == 15, "Max positions not saved correctly"
    
    # Test getting all settings
    all_settings = settings_manager.get_all_settings()
    print(f"All settings: {all_settings}")
    
    # Test reset to defaults
    print("\nTesting reset to defaults...")
    settings_manager.reset_to_defaults()
    
    threshold = settings_manager.get_blunder_threshold()
    depth = settings_manager.get_analysis_depth()
    max_pos = settings_manager.get_max_positions()
    
    print(f"After reset - Threshold: {threshold}, Depth: {depth}, Max positions: {max_pos}")
    assert threshold == 300, "Default threshold not set correctly"
    assert depth == 15, "Default depth not set correctly"
    assert max_pos == 20, "Default max positions not set correctly"
    
    # Username should still be there
    username = settings_manager.get_username()
    print(f"Username after reset: {username}")
    assert username == "testuser", "Username should persist after reset"
    
    conn.close()
    print("\n✅ All settings tests passed!")
    return True

if __name__ == "__main__":
    test_settings() 