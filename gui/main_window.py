#!/usr/bin/env python3
"""
Main Application Window for Chess Teacher
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
from typing import Optional, Dict, Any
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CHESS_COM_USERNAME
from gui.chess_board import ChessBoardWidget


class LoadingDialog:
    """Simple loading dialog for long operations."""
    
    def __init__(self, parent, title="Loading", message="Please wait..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("300x150")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 150,
            parent.winfo_rooty() + parent.winfo_height()//2 - 75
        ))
        
        # Content
        tk.Label(self.dialog, text=message, font=("Arial", 12)).pack(pady=20)
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start()
        
        # Prevent closing
        self.dialog.protocol("WM_DELETE_WINDOW", lambda: None)
    
    def close(self):
        """Close the loading dialog."""
        self.dialog.destroy()


class UsernameDialog:
    """Dialog for entering Chess.com username."""
    
    def __init__(self, parent):
        self.username = None
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Enter Chess.com Username")
        self.dialog.geometry("400x200")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center on parent
        self.dialog.geometry("+%d+%d" % (
            parent.winfo_rootx() + parent.winfo_width()//2 - 200,
            parent.winfo_rooty() + parent.winfo_height()//2 - 100
        ))
        
        # Content
        tk.Label(self.dialog, text="Enter your Chess.com username:", 
                font=("Arial", 12)).pack(pady=20)
        
        self.entry = tk.Entry(self.dialog, font=("Arial", 14), width=20)
        self.entry.pack(pady=10)
        self.entry.insert(0, CHESS_COM_USERNAME)
        self.entry.focus()
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="OK", command=self.ok_clicked, 
                 width=10).pack(side='left', padx=10)
        tk.Button(button_frame, text="Cancel", command=self.cancel_clicked, 
                 width=10).pack(side='left', padx=10)
        
        # Bind Enter key
        self.dialog.bind('<Return>', lambda e: self.ok_clicked())
        self.dialog.bind('<Escape>', lambda e: self.cancel_clicked())
    
    def ok_clicked(self):
        """Handle OK button click."""
        username = self.entry.get().strip()
        if username:
            self.username = username
            self.dialog.destroy()
        else:
            messagebox.showwarning("Invalid Username", "Please enter a valid username.")
    
    def cancel_clicked(self):
        """Handle Cancel button click."""
        self.dialog.destroy()


class BaseScreen:
    """Base class for all application screens."""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = tk.Frame(parent)
    
    def show(self):
        """Show this screen."""
        self.frame.pack(fill='both', expand=True)
    
    def hide(self):
        """Hide this screen."""
        self.frame.pack_forget()


class GameAnalysisScreen(BaseScreen):
    """Screen for analyzing games and viewing blunders."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the game analysis UI."""
        # Title
        title_label = tk.Label(self.frame, text="Game Analysis", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Username display
        self.username_label = tk.Label(self.frame, text="Username: Not set", 
                                      font=("Arial", 12))
        self.username_label.pack(pady=10)
        
        # Analysis controls
        controls_frame = tk.Frame(self.frame)
        controls_frame.pack(pady=20)
        
        tk.Button(controls_frame, text="Set Username", 
                 command=self.set_username).pack(side='left', padx=10)
        tk.Button(controls_frame, text="Analyze Games", 
                 command=self.analyze_games).pack(side='left', padx=10)
        tk.Button(controls_frame, text="View Blunders", 
                 command=self.view_blunders).pack(side='left', padx=10)
        
        # Status area
        self.status_label = tk.Label(self.frame, text="Ready to analyze games", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=20)
    
    def set_username(self):
        """Open username dialog."""
        dialog = UsernameDialog(self.parent)
        self.parent.wait_window(dialog.dialog)
        if dialog.username:
            self.username_label.config(text=f"Username: {dialog.username}")
            self.status_label.config(text=f"Username set to: {dialog.username}")
    
    def analyze_games(self):
        """Start game analysis (placeholder)."""
        self.status_label.config(text="Game analysis not yet implemented")
        messagebox.showinfo("Coming Soon", "Game analysis will be implemented in Section 9.")
    
    def view_blunders(self):
        """View blunders (placeholder)."""
        self.status_label.config(text="Blunder viewing not yet implemented")
        messagebox.showinfo("Coming Soon", "Blunder viewing will be implemented in Section 9.")


class TrainingSessionScreen(BaseScreen):
    """Screen for training sessions."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the training session UI."""
        # Title
        title_label = tk.Label(self.frame, text="Training Session", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Training controls
        controls_frame = tk.Frame(self.frame)
        controls_frame.pack(pady=20)
        
        tk.Button(controls_frame, text="Start Training", 
                 command=self.start_training).pack(side='left', padx=10)
        tk.Button(controls_frame, text="View Progress", 
                 command=self.view_progress).pack(side='left', padx=10)
        tk.Button(controls_frame, text="Settings", 
                 command=self.training_settings).pack(side='left', padx=10)
        
        # Status area
        self.status_label = tk.Label(self.frame, text="Ready to start training", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=20)
    
    def start_training(self):
        """Start training session (placeholder)."""
        self.status_label.config(text="Training not yet implemented")
        messagebox.showinfo("Coming Soon", "Training sessions will be implemented in Section 7.")
    
    def view_progress(self):
        """View training progress (placeholder)."""
        self.status_label.config(text="Progress viewing not yet implemented")
        messagebox.showinfo("Coming Soon", "Progress tracking will be implemented in Section 7.")
    
    def training_settings(self):
        """Open training settings (placeholder)."""
        self.status_label.config(text="Settings not yet implemented")
        messagebox.showinfo("Coming Soon", "Training settings will be implemented in Section 7.")


class SettingsScreen(BaseScreen):
    """Screen for application settings."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the settings UI."""
        # Title
        title_label = tk.Label(self.frame, text="Settings", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Settings content
        settings_frame = tk.Frame(self.frame)
        settings_frame.pack(pady=20, padx=50, fill='x')
        
        # Analysis settings
        analysis_frame = tk.LabelFrame(settings_frame, text="Analysis Settings", 
                                      font=("Arial", 12, "bold"))
        analysis_frame.pack(fill='x', pady=10)
        
        tk.Label(analysis_frame, text="Blunder Threshold (centipawns):").pack(anchor='w', padx=10, pady=5)
        self.threshold_var = tk.StringVar(value="300")
        tk.Entry(analysis_frame, textvariable=self.threshold_var, width=10).pack(anchor='w', padx=10, pady=5)
        
        tk.Label(analysis_frame, text="Analysis Depth:").pack(anchor='w', padx=10, pady=5)
        self.depth_var = tk.StringVar(value="15")
        tk.Entry(analysis_frame, textvariable=self.depth_var, width=10).pack(anchor='w', padx=10, pady=5)
        
        # Save button
        tk.Button(settings_frame, text="Save Settings", 
                 command=self.save_settings).pack(pady=20)
        
        # Status
        self.status_label = tk.Label(self.frame, text="Settings ready", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=20)
    
    def save_settings(self):
        """Save settings (placeholder)."""
        self.status_label.config(text="Settings saved (placeholder)")
        messagebox.showinfo("Settings", "Settings will be implemented in Section 9.")


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_screens()
        self.current_screen = None
        
        # Show default screen
        self.switch_screen("game_analysis")
    
    def setup_window(self):
        """Setup the main window properties."""
        self.root.title("Chess Teacher")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
    
    def setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Set Username", command=self.set_username)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Game Analysis", 
                                 command=lambda: self.switch_screen("game_analysis"))
        analysis_menu.add_command(label="View Blunders", 
                                 command=self.view_blunders)
        
        # Training menu
        training_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Training", menu=training_menu)
        training_menu.add_command(label="Training Session", 
                                 command=lambda: self.switch_screen("training_session"))
        training_menu.add_command(label="Progress Report", 
                                 command=self.view_progress)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Settings", 
                             command=lambda: self.switch_screen("settings"))
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, 
                                  anchor=tk.W, font=("Arial", 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_screens(self):
        """Setup all application screens."""
        self.screens: Dict[str, BaseScreen] = {
            "game_analysis": GameAnalysisScreen(self.root),
            "training_session": TrainingSessionScreen(self.root),
            "settings": SettingsScreen(self.root)
        }
    
    def switch_screen(self, screen_name: str):
        """Switch to a different screen."""
        if screen_name not in self.screens:
            messagebox.showerror("Error", f"Screen '{screen_name}' not found")
            return
        
        # Hide current screen
        if self.current_screen:
            self.current_screen.hide()
        
        # Show new screen
        self.screens[screen_name].show()
        self.current_screen = self.screens[screen_name]
        
        # Update status
        self.update_status(f"Switched to {screen_name.replace('_', ' ').title()}")
    
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def set_username(self):
        """Open username dialog."""
        dialog = UsernameDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.username:
            self.update_status(f"Username set to: {dialog.username}")
    
    def view_blunders(self):
        """View blunders (placeholder)."""
        messagebox.showinfo("Coming Soon", "Blunder viewing will be implemented in Section 9.")
    
    def view_progress(self):
        """View progress (placeholder)."""
        messagebox.showinfo("Coming Soon", "Progress tracking will be implemented in Section 7.")
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Chess Teacher v1.0

A chess training application that helps improve your game by:
• Analyzing your Chess.com games
• Identifying tactical mistakes
• Providing spaced repetition training

Built with Python, Tkinter, and Stockfish"""
        
        messagebox.showinfo("About Chess Teacher", about_text)
    
    def show_loading_dialog(self, title: str, message: str) -> LoadingDialog:
        """Show a loading dialog for long operations."""
        return LoadingDialog(self.root, title, message)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()


def main():
    """Main function to create and run the application."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main() 