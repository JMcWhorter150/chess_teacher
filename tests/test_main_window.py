#!/usr/bin/env python3
"""
Tests for MainWindow and related GUI components (Section 6)
"""

import pytest
import tkinter as tk
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import (
    MainWindow, 
    LoadingDialog, 
    UsernameDialog, 
    BaseScreen, 
    GameAnalysisScreen, 
    TrainingSessionScreen, 
    SettingsScreen
)


@pytest.fixture
def root_window():
    """Fixture to provide a root Tkinter window for testing."""
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    yield root
    root.destroy()


class TestLoadingDialog:
    """Test LoadingDialog functionality."""
    
    def test_loading_dialog_creation(self, root_window):
        """Test that LoadingDialog can be created."""
        dialog = LoadingDialog(root_window, "Test Loading", "Please wait...")
        
        assert dialog.dialog is not None
        assert dialog.dialog.title() == "Test Loading"
        assert dialog.progress is not None
        
        dialog.close()
    
    def test_loading_dialog_close(self, root_window):
        """Test that LoadingDialog can be closed."""
        dialog = LoadingDialog(root_window, "Test Loading", "Please wait...")
        
        # Dialog should exist
        assert dialog.dialog.winfo_exists()
        
        # Close dialog
        dialog.close()
        
        # Dialog should be destroyed
        assert not dialog.dialog.winfo_exists()


class TestUsernameDialog:
    """Test UsernameDialog functionality."""
    
    def test_username_dialog_creation(self, root_window):
        """Test that UsernameDialog can be created."""
        dialog = UsernameDialog(root_window)
        
        assert dialog.dialog is not None
        assert dialog.dialog.title() == "Enter Chess.com Username"
        assert dialog.entry is not None
        
        dialog.dialog.destroy()
    
    def test_username_dialog_ok_with_valid_username(self, root_window):
        """Test OK button with valid username."""
        dialog = UsernameDialog(root_window)
        
        # Set a valid username
        dialog.entry.delete(0, tk.END)
        dialog.entry.insert(0, "testuser")
        
        # Simulate OK click
        dialog.ok_clicked()
        
        assert dialog.username == "testuser"
        assert not dialog.dialog.winfo_exists()
    
    def test_username_dialog_ok_with_empty_username(self, root_window):
        """Test OK button with empty username."""
        dialog = UsernameDialog(root_window)
        
        # Clear username
        dialog.entry.delete(0, tk.END)
        
        # Mock messagebox.showwarning to avoid actual dialog
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            dialog.ok_clicked()
            
            # Should show warning and not close dialog
            mock_warning.assert_called_once()
            assert dialog.dialog.winfo_exists()
            assert dialog.username is None
        
        dialog.dialog.destroy()
    
    def test_username_dialog_cancel(self, root_window):
        """Test Cancel button."""
        dialog = UsernameDialog(root_window)
        
        # Simulate Cancel click
        dialog.cancel_clicked()
        
        assert dialog.username is None
        assert not dialog.dialog.winfo_exists()


class TestBaseScreen:
    """Test BaseScreen functionality."""
    
    def test_base_screen_creation(self, root_window):
        """Test that BaseScreen can be created."""
        screen = BaseScreen(root_window)
        
        assert screen.parent == root_window
        assert screen.frame is not None
    
    def test_base_screen_show_hide(self, root_window):
        """Test show and hide methods."""
        screen = BaseScreen(root_window)
        
        # Initially not shown (frame exists but not packed)
        assert screen.frame is not None
        
        # Show screen
        screen.show()
        # Frame should be packed (we can't easily test winfo_ismapped in test environment)
        assert screen.frame is not None
        
        # Hide screen
        screen.hide()
        # Frame should still exist but not be packed
        assert screen.frame is not None


class TestGameAnalysisScreen:
    """Test GameAnalysisScreen functionality."""
    
    def test_game_analysis_screen_creation(self, root_window):
        """Test that GameAnalysisScreen can be created."""
        screen = GameAnalysisScreen(root_window)
        
        assert isinstance(screen, BaseScreen)
        assert screen.username_label is not None
        assert screen.status_label is not None
    
    def test_game_analysis_screen_set_username(self, root_window):
        """Test set_username method."""
        screen = GameAnalysisScreen(root_window)
        
        # Mock UsernameDialog to return a username
        mock_dialog = MagicMock()
        mock_dialog.username = "testuser"
        
        with patch('gui.main_window.UsernameDialog', return_value=mock_dialog):
            screen.set_username()
            
            # Should update username label and status
            assert "testuser" in screen.username_label.cget("text")
            assert "testuser" in screen.status_label.cget("text")


class TestTrainingSessionScreen:
    """Test TrainingSessionScreen functionality."""
    
    def test_training_session_screen_creation(self, root_window):
        """Test that TrainingSessionScreen can be created."""
        screen = TrainingSessionScreen(root_window)
        
        assert isinstance(screen, BaseScreen)
        assert screen.status_label is not None
    
    def test_training_session_screen_placeholder_methods(self, root_window):
        """Test placeholder methods show appropriate messages."""
        screen = TrainingSessionScreen(root_window)
        
        # Test start_training
        screen.start_training()
        assert "not yet implemented" in screen.status_label.cget("text")
        
        # Test view_progress
        screen.view_progress()
        assert "not yet implemented" in screen.status_label.cget("text")
        
        # Test training_settings
        screen.training_settings()
        assert "not yet implemented" in screen.status_label.cget("text")


class TestSettingsScreen:
    """Test SettingsScreen functionality."""
    
    def test_settings_screen_creation(self, root_window):
        """Test that SettingsScreen can be created."""
        screen = SettingsScreen(root_window)
        
        assert isinstance(screen, BaseScreen)
        assert screen.threshold_var is not None
        assert screen.depth_var is not None
        assert screen.status_label is not None
        
        # Check default values
        assert screen.threshold_var.get() == "300"
        assert screen.depth_var.get() == "15"
    
    def test_settings_screen_save_settings(self, root_window):
        """Test save_settings method."""
        screen = SettingsScreen(root_window)
        
        # Change values
        screen.threshold_var.set("400")
        screen.depth_var.set("20")
        
        # Mock messagebox.showinfo to avoid actual dialog
        with patch('tkinter.messagebox.showinfo') as mock_info:
            screen.save_settings()
            
            # Should show info dialog and update status
            mock_info.assert_called_once()
            assert "saved" in screen.status_label.cget("text")


class TestMainWindow:
    """Test MainWindow functionality."""
    
    def test_main_window_creation(self):
        """Test that MainWindow can be created."""
        app = MainWindow()
        
        assert app.root is not None
        assert app.root.title() == "Chess Teacher"
        assert app.status_bar is not None
        assert app.current_screen is not None
        
        # Check that screens are created
        assert "game_analysis" in app.screens
        assert "training_session" in app.screens
        assert "settings" in app.screens
        
        app.root.destroy()
    
    def test_main_window_switch_screen(self):
        """Test switch_screen method."""
        app = MainWindow()
        
        # Start with game_analysis screen
        assert app.current_screen == app.screens["game_analysis"]
        
        # Switch to training session
        app.switch_screen("training_session")
        assert app.current_screen == app.screens["training_session"]
        
        # Switch to settings
        app.switch_screen("settings")
        assert app.current_screen == app.screens["settings"]
        
        app.root.destroy()
    
    def test_main_window_switch_invalid_screen(self):
        """Test switch_screen with invalid screen name."""
        app = MainWindow()
        
        # Mock messagebox.showerror to avoid actual dialog
        with patch('tkinter.messagebox.showerror') as mock_error:
            app.switch_screen("invalid_screen")
            
            # Should show error dialog
            mock_error.assert_called_once()
            
            # Current screen should not change
            assert app.current_screen == app.screens["game_analysis"]
        
        app.root.destroy()
    
    def test_main_window_update_status(self):
        """Test update_status method."""
        app = MainWindow()
        
        test_message = "Test status message"
        app.update_status(test_message)
        
        assert app.status_bar.cget("text") == test_message
        
        app.root.destroy()
    
    def test_main_window_set_username(self):
        """Test set_username method."""
        app = MainWindow()
        
        # Mock UsernameDialog to return a username
        mock_dialog = MagicMock()
        mock_dialog.username = "testuser"
        
        with patch('gui.main_window.UsernameDialog', return_value=mock_dialog):
            app.set_username()
            
            # Should update status
            assert "testuser" in app.status_bar.cget("text")
        
        app.root.destroy()
    
    def test_main_window_placeholder_methods(self):
        """Test placeholder methods show appropriate dialogs."""
        app = MainWindow()
        
        # Mock messagebox.showinfo to avoid actual dialogs
        with patch('tkinter.messagebox.showinfo') as mock_info:
            # Test view_blunders
            app.view_blunders()
            mock_info.assert_called_with("Coming Soon", "Blunder viewing will be implemented in Section 9.")
            
            # Test view_progress
            app.view_progress()
            mock_info.assert_called_with("Coming Soon", "Progress tracking will be implemented in Section 7.")
            
            # Test show_about
            app.show_about()
            mock_info.assert_called_with("About Chess Teacher", pytest.approx("Chess Teacher v1.0"))
        
        app.root.destroy()
    
    def test_main_window_show_loading_dialog(self):
        """Test show_loading_dialog method."""
        app = MainWindow()
        
        dialog = app.show_loading_dialog("Test Loading", "Please wait...")
        
        assert isinstance(dialog, LoadingDialog)
        assert dialog.dialog.title() == "Test Loading"
        
        dialog.close()
        app.root.destroy()


class TestMainWindowIntegration:
    """Integration tests for MainWindow."""
    
    def test_main_window_menu_structure(self):
        """Test that menu structure is correct."""
        app = MainWindow()
        
        # Check that menu bar exists
        menubar = app.root.config('menu')
        assert menubar is not None
        
        # Check menu items (basic structure)
        menu_items = [child.entrycget(0, 'label') for child in menubar.winfo_children()]
        expected_menus = ['File', 'Analysis', 'Training', 'Help']
        
        for expected_menu in expected_menus:
            assert expected_menu in menu_items
        
        app.root.destroy()
    
    def test_main_window_window_properties(self):
        """Test window properties are set correctly."""
        app = MainWindow()
        
        # Check window properties
        assert app.root.title() == "Chess Teacher"
        assert app.root.winfo_width() >= 600  # minsize
        assert app.root.winfo_height() >= 400  # minsize
        
        app.root.destroy()


if __name__ == "__main__":
    pytest.main([__file__]) 