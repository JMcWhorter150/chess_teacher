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
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import CHESS_COM_USERNAME, DATABASE_PATH
from gui.chess_board import ChessBoardWidget
from gui.training_interface import TrainingScreen
from data.database import create_connection, insert_game, get_games_by_username, get_blunders_by_username, SettingsManager
from data.models import Game, Review
from chess_api.chess_com_client import get_recent_games
from utils.pgn_parser import parse_pgn_string
from analysis.position_analyzer import find_blunders
from analysis.stockfish_analyzer import StockfishAnalyzer
from training.session_manager import TrainingSession

logger = logging.getLogger(__name__)

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
        self.parent = parent  # This will now be the MainWindow instance
        # Handle both MainWindow objects (with .root) and tk.Tk objects (for testing)
        if hasattr(parent, 'root'):
            self.frame = tk.Frame(parent.root)
        else:
            # For testing when parent is directly a tk.Tk object
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
        self.username = None
        self.analyzer = None
        self.settings_manager = None
        self.setup_ui()
        self.load_settings()
    
    def show(self):
        """Show this screen and refresh statistics."""
        super().show()
        # Refresh statistics when screen is shown
        if self.username:
            self.load_statistics()
    
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
        
        # Progress frame
        self.progress_frame = tk.Frame(self.frame)
        self.progress_frame.pack(pady=10, fill='x', padx=20)
        
        self.progress_label = tk.Label(self.progress_frame, text="", 
                                      font=("Arial", 10))
        self.progress_label.pack()
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='determinate')
        self.progress_bar.pack(fill='x', pady=5)
        
        # Status area
        self.status_label = tk.Label(self.frame, text="Ready to analyze games", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=20)
        
        # Statistics frame
        self.stats_frame = tk.Frame(self.frame)
        self.stats_frame.pack(pady=10, fill='x', padx=20)
        
        self.games_label = tk.Label(self.stats_frame, text="Games analyzed: 0", 
                                   font=("Arial", 10))
        self.games_label.pack()
        
        self.blunders_label = tk.Label(self.stats_frame, text="Blunders found: 0", 
                                      font=("Arial", 10))
        self.blunders_label.pack()
    
    def load_settings(self):
        """Load saved settings."""
        try:
            # Create database connection and settings manager
            conn = create_connection(DATABASE_PATH)
            if conn:
                self.settings_manager = SettingsManager(conn)
                self.username = self.settings_manager.get_username()
                logger.info(f"Loaded username from database: {self.username}")
                if self.username:
                    self.username_label.config(text=f"Username: {self.username}")
                    # Load existing statistics for this username
                    self.load_statistics()
                conn.close()
            else:
                logger.warning("Could not connect to database to load settings")
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
    
    def load_statistics(self):
        """Load existing statistics from the database."""
        if not self.username:
            return
        
        try:
            conn = create_connection(DATABASE_PATH)
            if not conn:
                logger.warning("Could not connect to database to load statistics")
                return
            
            # Get games count
            games = get_games_by_username(conn, self.username)
            games_count = len(games)
            
            # Get blunders count
            blunders = get_blunders_by_username(conn, self.username)
            blunders_count = len(blunders)
            
            conn.close()
            
            # Update UI
            self.games_label.config(text=f"Games analyzed: {games_count}")
            self.blunders_label.config(text=f"Blunders found: {blunders_count}")
            
            logger.info(f"Loaded statistics: {games_count} games, {blunders_count} blunders")
            
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
    
    def save_settings(self):
        """Save current settings."""
        try:
            conn = create_connection(DATABASE_PATH)
            if conn:
                settings_manager = SettingsManager(conn)
                # Save all settings
                settings_manager.set_blunder_threshold(int(self.threshold_var.get()))
                settings_manager.set_analysis_depth(int(self.depth_var.get()))
                settings_manager.set_max_positions(int(self.max_positions_var.get()))
                conn.close()
                logger.info("Settings saved to database")
                messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            else:
                logger.error("Could not connect to database to save settings")
                messagebox.showerror("Save Error", "Could not connect to database to save settings")
        except Exception as e:
            logger.error(f"Could not save settings: {e}")
            messagebox.showerror("Save Error", f"Could not save settings: {e}")
    
    def set_username(self):
        """Set the Chess.com username."""
        username = simpledialog.askstring("Set Username", "Enter your Chess.com username:")
        if username:
            self.username = username
            self.username_label.config(text=f"Username: {username}")
            # Save to settings
            try:
                conn = create_connection(DATABASE_PATH)
                if conn:
                    settings_manager = SettingsManager(conn)
                    settings_manager.set_username(username)
                    conn.close()
                    logger.info(f"Username saved to database: {username}")
                else:
                    logger.error("Could not connect to database to save username")
            except Exception as e:
                logger.error(f"Could not save username: {e}")
            messagebox.showinfo("Username Set", f"Username set to: {username}")
    
    def analyze_games(self):
        """Analyze games for the current username."""
        if not self.username:
            messagebox.showwarning("No Username", "Please set a username first.")
            return
        
        # Get analysis parameters from settings
        try:
            conn = create_connection(DATABASE_PATH)
            if conn:
                settings_manager = SettingsManager(conn)
                blunder_threshold = settings_manager.get_blunder_threshold()
                analysis_depth = settings_manager.get_analysis_depth()
                conn.close()
            else:
                # Use defaults if database connection fails
                blunder_threshold = 300
                analysis_depth = 15
                logger.warning("Could not connect to database, using default settings")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            blunder_threshold = 300
            analysis_depth = 15
        
        def analyze_thread():
            try:
                self.status_label.config(text="Fetching games from Chess.com...")
                self.progress_bar.start()
                
                # Fetch games from Chess.com
                games_data = get_recent_games(self.username, count=50)
                if not games_data:
                    self.status_label.config(text="No games found or error fetching games")
                    self.progress_bar.stop()
                    return
                
                self.status_label.config(text=f"Found {len(games_data)} games. Analyzing...")
                
                # Initialize Stockfish analyzer
                self.analyzer = StockfishAnalyzer()
                if not self.analyzer.is_available():
                    self.status_label.config(text="Stockfish not available. Please install Stockfish.")
                    self.progress_bar.stop()
                    return
                
                # Process each game
                conn = create_connection(DATABASE_PATH)
                if not conn:
                    self.status_label.config(text="Database connection failed")
                    self.progress_bar.stop()
                    return
                
                games_processed = 0
                blunders_found = 0
                
                for game_data in games_data:
                    try:
                        # Parse PGN
                        game = parse_pgn_string(game_data, self.username)
                        if not game:
                            continue
                        
                        # Check if game already exists
                        existing_games = get_games_by_username(conn, self.username)
                        if any(g.pgn == game.pgn for g in existing_games):
                            continue
                        
                        # Insert game
                        game_id = insert_game(conn, game)
                        
                        # Find blunders
                        blunders = find_blunders(game, threshold=blunder_threshold)
                        for blunder in blunders:
                            blunder.game_id = game_id
                            insert_blunder(conn, blunder)
                            blunders_found += 1
                        
                        games_processed += 1
                        
                    except Exception as e:
                        logger.error(f"Error processing game: {e}")
                        continue
                
                conn.close()
                
                self.status_label.config(text=f"Analysis complete! Processed {games_processed} games, found {blunders_found} blunders")
                self.progress_bar.stop()
                
                # Refresh statistics
                self.load_statistics()
                
            except Exception as e:
                logger.error(f"Error in analysis thread: {e}")
                self.status_label.config(text=f"Analysis failed: {e}")
                self.progress_bar.stop()
        
        # Run analysis in background thread
        thread = threading.Thread(target=analyze_thread)
        thread.daemon = True
        thread.start()
    
    def view_blunders(self):
        """View blunders for the current username."""
        if not self.username:
            messagebox.showwarning("No Username", "Please set a username first.")
            return
        
        try:
            conn = create_connection(DATABASE_PATH)
            if not conn:
                messagebox.showerror("Database Error", "Could not connect to database.")
                return
            
            # Debug: Check what's in the database
            logger.info(f"Looking for blunders for username: {self.username}")
            
            blunders = get_blunders_by_username(conn, self.username)
            logger.info(f"Found {len(blunders)} blunders for {self.username}")
            
            conn.close()
            
            if not blunders:
                messagebox.showinfo("No Blunders", "No blunders found for this username.")
                return
            
            # Get max positions setting
            try:
                conn = create_connection(DATABASE_PATH)
                if conn:
                    settings_manager = SettingsManager(conn)
                    max_positions = settings_manager.get_max_positions()
                    conn.close()
                else:
                    max_positions = 20
                    logger.warning("Could not connect to database, using default max positions")
            except Exception as e:
                logger.error(f"Error loading max positions setting: {e}")
                max_positions = 20
            
            # Switch to training session with blunders
            self.parent.switch_screen("training_session")
            
            # Get the training session screen and start training with blunders
            training_session_screen = self.parent.screens["training_session"]
            training_session_screen.start_training_with_blunders(blunders[:max_positions])
            
        except Exception as e:
            logger.error(f"Error viewing blunders: {e}")
            messagebox.showerror("Error", f"Could not load blunders: {e}")


class TrainingSessionScreen(BaseScreen):
    """Screen for training sessions."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.username = None
        self.training_session = None
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the training session UI."""
        # Title
        title_label = tk.Label(self.frame, text="Training Session", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Username display
        self.username_label = tk.Label(self.frame, text="Username: Not set", 
                                      font=("Arial", 12))
        self.username_label.pack(pady=10)
        
        # Training controls
        controls_frame = tk.Frame(self.frame)
        controls_frame.pack(pady=20)
        
        tk.Button(controls_frame, text="Set Username", 
                 command=self.set_username).pack(side='left', padx=10)
        tk.Button(controls_frame, text="Start Training", 
                 command=self.start_training).pack(side='left', padx=10)
        tk.Button(controls_frame, text="View Progress", 
                 command=self.view_progress).pack(side='left', padx=10)
        
        # Training interface
        self.training_frame = tk.Frame(self.frame)
        self.training_frame.pack(pady=20, fill='both', expand=True)
        
        # Status area
        self.status_label = tk.Label(self.frame, text="Ready to start training", 
                                    font=("Arial", 10), fg="gray")
        self.status_label.pack(pady=20)
    
    def load_settings(self):
        """Load saved settings."""
        try:
            if os.path.exists('settings.json'):
                with open('settings.json', 'r') as f:
                    settings = json.load(f)
                    self.username = settings.get('username')
                    if self.username:
                        self.username_label.config(text=f"Username: {self.username}")
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
    
    def set_username(self):
        """Open username dialog."""
        dialog = UsernameDialog(self.parent.root)
        self.parent.root.wait_window(dialog.dialog)
        if dialog.username:
            self.username = dialog.username
            self.username_label.config(text=f"Username: {self.username}")
            self.status_label.config(text=f"Username set to: {self.username}")
    
    def start_training(self):
        """Start a training session."""
        if not self.username:
            messagebox.showwarning("No Username", "Please set a username first.")
            return
        
        try:
            logger.info("Creating TrainingSession...")
            # Create training session
            self.training_session = TrainingSession(self.username)
            
            logger.info("Checking available positions...")
            # Check if there are positions available
            if not self.training_session.available_positions:
                messagebox.showinfo("No Positions", "No training positions available. Please analyze some games first.")
                return
            
            logger.info("Creating TrainingScreen...")
            # Create training interface
            # Clear any existing training screen
            for widget in self.training_frame.winfo_children():
                widget.destroy()
            
            self.training_screen = TrainingScreen(self.training_frame, self.training_session)
            logger.info("Packing TrainingScreen...")
            self.training_screen.pack(fill='both', expand=True)
            
            self.status_label.config(text="Training session started")
            
        except Exception as e:
            logger.error(f"Error starting training: {e}")
            messagebox.showerror("Training Error", f"Could not start training: {e}")
    
    def start_training_with_blunders(self, blunders):
        """Start a training session with specific blunders."""
        if not self.username:
            messagebox.showwarning("No Username", "Please set a username first.")
            return
        
        try:
            logger.info(f"Creating TrainingSession for {len(blunders)} blunders...")
            # Create a custom training session with the provided blunders
            self.training_session = TrainingSession(self.username, auto_load_positions=False)
            
            # Convert blunders to the format expected by training interface
            # Each blunder needs a review record (even if it's a new one)
            from datetime import date
            
            logger.info("Creating blunder-review pairs...")
            blunder_review_pairs = []
            for blunder in blunders:
                # Create a new review record for each blunder
                review = Review(
                    id=0,
                    blunder_id=blunder.id,
                    last_reviewed="",
                    next_review=date.today().isoformat(),
                    ease_factor=2.5,
                    repetition_count=0,
                    correct_streak=0
                )
                blunder_review_pairs.append((blunder, review))
            
            # Set the available positions to our blunders
            self.training_session.available_positions = blunder_review_pairs
            self.training_session.current_position_index = 0
            
            logger.info(f"Set {len(blunder_review_pairs)} positions in training session")
            logger.info(f"Available positions count: {len(self.training_session.available_positions)}")
            
            # Clear any existing training screen
            for widget in self.training_frame.winfo_children():
                widget.destroy()
            
            logger.info("Creating TrainingScreen...")
            # Create training interface
            self.training_screen = TrainingScreen(self.training_frame, self.training_session)
            logger.info("Packing TrainingScreen...")
            self.training_screen.pack(fill='both', expand=True)
            
            self.status_label.config(text=f"Training session started with {len(blunders)} blunders")
            
        except Exception as e:
            logger.error(f"Error starting training with blunders: {e}")
            messagebox.showerror("Training Error", f"Could not start training: {e}")
    
    def view_progress(self):
        """View training progress."""
        if not self.username:
            messagebox.showwarning("No Username", "Please set a username first.")
            return
        
        try:
            session = TrainingSession(self.username)
            stats = session.get_review_schedule_info()
            
            progress_text = f"Training Progress for {self.username}:\n\n"
            progress_text += f"Positions due for review: {stats['total_due']}\n"
            progress_text += f"New positions: {stats['new_positions']}\n"
            progress_text += f"Repeat positions: {stats['repeat_positions']}\n"
            progress_text += f"Retention rate: {stats['retention_rate']:.1f}%\n"
            progress_text += f"Average ease factor: {stats['average_ease_factor']:.2f}\n"
            progress_text += f"Total reviews: {stats['total_reviews']}"
            
            messagebox.showinfo("Training Progress", progress_text)
            
        except Exception as e:
            logger.error(f"Error viewing progress: {e}")
            messagebox.showerror("Error", f"Could not load progress: {e}")


class SettingsScreen(BaseScreen):
    """Screen for application settings."""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        self.load_settings()
    
    def setup_ui(self):
        """Setup the settings UI."""
        # Title
        title_label = tk.Label(self.frame, text="Settings", 
                              font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Settings frame
        settings_frame = tk.Frame(self.frame)
        settings_frame.pack(pady=20, padx=20, fill='x')
        
        # Analysis settings
        analysis_frame = tk.LabelFrame(settings_frame, text="Analysis Settings", padx=10, pady=10)
        analysis_frame.pack(fill='x', pady=10)
        
        tk.Label(analysis_frame, text="Blunder threshold (centipawns):").pack(anchor='w')
        self.threshold_var = tk.StringVar(value="300")
        tk.Entry(analysis_frame, textvariable=self.threshold_var, width=10).pack(anchor='w')
        
        tk.Label(analysis_frame, text="Analysis depth:").pack(anchor='w')
        self.depth_var = tk.StringVar(value="15")
        tk.Entry(analysis_frame, textvariable=self.depth_var, width=10).pack(anchor='w')
        
        # Training settings
        training_frame = tk.LabelFrame(settings_frame, text="Training Settings", padx=10, pady=10)
        training_frame.pack(fill='x', pady=10)
        
        tk.Label(training_frame, text="Max positions per session:").pack(anchor='w')
        self.max_positions_var = tk.StringVar(value="20")
        tk.Entry(training_frame, textvariable=self.max_positions_var, width=10).pack(anchor='w')
        
        # Buttons
        button_frame = tk.Frame(settings_frame)
        button_frame.pack(pady=20)
        
        tk.Button(button_frame, text="Save Settings", 
                 command=self.save_settings).pack(side='left', padx=10)
        tk.Button(button_frame, text="Reset to Defaults", 
                 command=self.reset_settings).pack(side='left', padx=10)
    
    def load_settings(self):
        """Load saved settings."""
        try:
            conn = create_connection(DATABASE_PATH)
            if conn:
                settings_manager = SettingsManager(conn)
                self.threshold_var.set(str(settings_manager.get_blunder_threshold()))
                self.depth_var.set(str(settings_manager.get_analysis_depth()))
                self.max_positions_var.set(str(settings_manager.get_max_positions()))
                conn.close()
            else:
                logger.warning("Could not connect to database to load settings")
        except Exception as e:
            logger.warning(f"Could not load settings: {e}")
    
    def save_settings(self):
        """Save current settings."""
        try:
            conn = create_connection(DATABASE_PATH)
            if conn:
                settings_manager = SettingsManager(conn)
                # Save all settings
                settings_manager.set_blunder_threshold(int(self.threshold_var.get()))
                settings_manager.set_analysis_depth(int(self.depth_var.get()))
                settings_manager.set_max_positions(int(self.max_positions_var.get()))
                conn.close()
                logger.info("Settings saved to database")
                messagebox.showinfo("Settings Saved", "Settings have been saved successfully.")
            else:
                logger.error("Could not connect to database to save settings")
                messagebox.showerror("Save Error", "Could not connect to database to save settings")
        except Exception as e:
            logger.error(f"Could not save settings: {e}")
            messagebox.showerror("Save Error", f"Could not save settings: {e}")
    
    def reset_settings(self):
        """Reset settings to defaults."""
        try:
            conn = create_connection(DATABASE_PATH)
            if conn:
                settings_manager = SettingsManager(conn)
                settings_manager.reset_to_defaults()
                # Reload the settings to update the UI
                self.load_settings()
                conn.close()
                messagebox.showinfo("Settings Reset", "Settings have been reset to defaults.")
            else:
                logger.error("Could not connect to database to reset settings")
                messagebox.showerror("Reset Error", "Could not connect to database to reset settings")
        except Exception as e:
            logger.error(f"Could not reset settings: {e}")
            messagebox.showerror("Reset Error", f"Could not reset settings: {e}")


class MainWindow:
    """Main application window."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.current_screen = None
        self.screens = {}
        
        self.setup_window()
        self.setup_menu()
        self.setup_status_bar()
        self.setup_screens()
        
        # Show default screen
        self.switch_screen("game_analysis")
    
    def setup_window(self):
        """Setup the main window."""
        self.root.title("Chess Teacher")
        self.root.geometry("1000x800")
        self.root.minsize(800, 700)
        
        # Center window on screen
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f"1000x800+{x}+{y}")
    
    def setup_menu(self):
        """Setup the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Game Analysis", command=lambda: self.switch_screen("game_analysis"))
        file_menu.add_command(label="Training Session", command=lambda: self.switch_screen("training_session"))
        file_menu.add_separator()
        file_menu.add_command(label="Settings", command=lambda: self.switch_screen("settings"))
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Analysis menu
        analysis_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Analyze Games", command=self.analyze_games)
        analysis_menu.add_command(label="View Blunders", command=self.view_blunders)
        
        # Training menu
        training_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Training", menu=training_menu)
        training_menu.add_command(label="Start Training", command=self.start_training)
        training_menu.add_command(label="View Progress", command=self.view_progress)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_screens(self):
        """Setup all application screens."""
        self.screens = {
            "game_analysis": GameAnalysisScreen(self),
            "training_session": TrainingSessionScreen(self),
            "settings": SettingsScreen(self)
        }
    
    def switch_screen(self, screen_name: str):
        """Switch to a different screen."""
        if self.current_screen:
            self.current_screen.hide()
        
        if screen_name in self.screens:
            self.current_screen = self.screens[screen_name]
            self.current_screen.show()
            self.update_status(f"Switched to {screen_name.replace('_', ' ').title()}")
        else:
            # Show error for invalid screen name
            messagebox.showerror("Invalid Screen", f"Screen '{screen_name}' not found.")
    
    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_bar.config(text=message)
        logger.info(f"Status: {message}")
    
    def set_username(self):
        """Set username for the application."""
        dialog = UsernameDialog(self.root)
        self.root.wait_window(dialog.dialog)
        if dialog.username:
            # Update all screens with the new username
            for screen in self.screens.values():
                if hasattr(screen, 'username'):
                    screen.username = dialog.username
                    if hasattr(screen, 'username_label'):
                        screen.username_label.config(text=f"Username: {dialog.username}")
    
    def analyze_games(self):
        """Start game analysis."""
        if "game_analysis" in self.screens:
            self.screens["game_analysis"].analyze_games()
    
    def view_blunders(self):
        """View blunders."""
        if "game_analysis" in self.screens:
            self.screens["game_analysis"].view_blunders()
    
    def start_training(self):
        """Start training session."""
        if "training_session" in self.screens:
            self.screens["training_session"].start_training()
    
    def view_progress(self):
        """View training progress."""
        if "training_session" in self.screens:
            self.screens["training_session"].view_progress()
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Chess Teacher v1.0

A chess training application that helps improve your game by:
• Analyzing your Chess.com games for blunders
• Creating training positions from your mistakes
• Using spaced repetition for optimal learning

Built with Python, Tkinter, and Stockfish."""
        
        messagebox.showinfo("About Chess Teacher", about_text)
    
    def show_loading_dialog(self, title: str, message: str) -> LoadingDialog:
        """Show a loading dialog."""
        return LoadingDialog(self.root, title, message)
    
    def run(self):
        """Run the main application loop."""
        self.root.mainloop()


def main():
    """Main function for testing."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main() 