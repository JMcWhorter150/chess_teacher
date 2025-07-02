import chess
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from datetime import datetime
import time

from .chess_board import ChessBoardWidget
from data.models import Blunder, Review
from data.database import create_connection
from config.settings import DATABASE_PATH


class TrainingScreen(tk.Frame):
    """
    Training interface for practicing blunder positions.
    """
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.parent = parent
        
        # Training state
        self.current_blunder: Optional[Blunder] = None
        self.current_review: Optional[Review] = None
        self.start_time: Optional[float] = None
        self.move_made = False
        self.correct_answer = False
        
        # Callbacks
        self.on_position_complete: Optional[Callable[[int, bool, float], None]] = None
        self.on_session_end: Optional[Callable[[], None]] = None
        
        # Session statistics
        self.positions_attempted = 0
        self.correct_answers = 0
        self.total_time = 0.0
        
        self.setup_ui()
    
    def setup_ui(self):
        """Create the training interface layout."""
        # Main container
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Top section - Position info and controls
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Position information
        self.position_info = ttk.Label(top_frame, text="Loading position...", 
                                      font=("Arial", 12, "bold"))
        self.position_info.pack(side=tk.LEFT)
        
        # Session statistics
        self.stats_label = ttk.Label(top_frame, text="0/0 correct", 
                                    font=("Arial", 10))
        self.stats_label.pack(side=tk.RIGHT)
        
        # Chess board (center)
        board_frame = ttk.Frame(main_frame)
        board_frame.pack(expand=True, pady=10)
        
        self.chess_board = ChessBoardWidget(board_frame, size=400)
        self.chess_board.pack()
        self.chess_board.set_move_callback(self.on_move_made)
        
        # Feedback area
        feedback_frame = ttk.Frame(main_frame)
        feedback_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.feedback_label = ttk.Label(feedback_frame, text="", 
                                       font=("Arial", 11), wraplength=500)
        self.feedback_label.pack()
        
        # Navigation buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.show_solution_btn = ttk.Button(button_frame, text="Show Solution", 
                                           command=self.show_solution)
        self.show_solution_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.next_position_btn = ttk.Button(button_frame, text="Next Position", 
                                           command=self.next_position)
        self.next_position_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.end_session_btn = ttk.Button(button_frame, text="End Session", 
                                         command=self.end_session)
        self.end_session_btn.pack(side=tk.RIGHT)
        
        # Initially disable buttons
        self.show_solution_btn.config(state=tk.DISABLED)
        self.next_position_btn.config(state=tk.DISABLED)
    
    def load_training_position(self, blunder: Blunder, review: Optional[Review] = None):
        """Load a training position from a blunder."""
        self.current_blunder = blunder
        self.current_review = review
        self.move_made = False
        self.correct_answer = False
        self.start_time = time.time()
        
        # Set up the position
        board = chess.Board(blunder.fen_before)
        self.chess_board.set_position(board)
        
        # Determine whose turn it is
        turn_color = "White" if board.turn else "Black"
        
        # Update position info
        info_text = f"Find the best move for {turn_color} in this position"
        if blunder.move_number:
            info_text += f" (Move {blunder.move_number})"
        self.position_info.config(text=info_text)
        
        # Clear feedback
        self.feedback_label.config(text="")
        
        # Reset button states
        self.show_solution_btn.config(state=tk.NORMAL)
        self.next_position_btn.config(state=tk.DISABLED)
        
        # Update statistics
        self.update_stats_display()
    
    def on_move_made(self, move: chess.Move):
        """Handle when a move is made on the chess board."""
        if self.move_made or not self.current_blunder:
            return
        
        self.move_made = True
        move_uci = move.uci()
        best_move_uci = self.current_blunder.best_move
        
        # Check if the move is correct
        self.correct_answer = (move_uci == best_move_uci)
        
        # Calculate time taken
        time_taken = time.time() - self.start_time
        
        # Update statistics
        self.positions_attempted += 1
        if self.correct_answer:
            self.correct_answers += 1
        self.total_time += time_taken
        
        # Show feedback
        if self.correct_answer:
            self.feedback_label.config(
                text=f"Correct! Your move {move_uci} was the best move. "
                     f"Time: {time_taken:.1f}s",
                foreground="green"
            )
        else:
            self.feedback_label.config(
                text=f"Incorrect. Your move: {move_uci}, Best move: {best_move_uci}. "
                     f"Time: {time_taken:.1f}s",
                foreground="red"
            )
        
        # Update button states
        self.show_solution_btn.config(state=tk.DISABLED)
        self.next_position_btn.config(state=tk.NORMAL)
        
        # Update statistics display
        self.update_stats_display()
        
        # Call completion callback if set
        if self.on_position_complete:
            self.on_position_complete(
                self.current_blunder.id, 
                self.correct_answer, 
                time_taken
            )
    
    def show_solution(self):
        """Show the solution for the current position."""
        if not self.current_blunder:
            return
        
        # Create a board with the position
        board = chess.Board(self.current_blunder.fen_before)
        
        # Make the best move to show the result
        best_move = chess.Move.from_uci(self.current_blunder.best_move)
        board.push(best_move)
        
        # Update the board display
        self.chess_board.set_position(board)
        
        # Update feedback
        self.feedback_label.config(
            text=f"Solution: {self.current_blunder.best_move} "
                 f"(Evaluation change: {self.current_blunder.centipawn_loss} centipawns)",
            foreground="blue"
        )
        
        # Disable show solution button
        self.show_solution_btn.config(state=tk.DISABLED)
    
    def next_position(self):
        """Move to the next training position."""
        # Reset the board to the original position
        if self.current_blunder:
            board = chess.Board(self.current_blunder.fen_before)
            self.chess_board.set_position(board)
        
        # Clear feedback
        self.feedback_label.config(text="")
        
        # Reset button states
        self.show_solution_btn.config(state=tk.NORMAL)
        self.next_position_btn.config(state=tk.DISABLED)
        
        # Signal that we're ready for the next position
        # This will be handled by the session manager
        pass
    
    def end_session(self):
        """End the current training session."""
        if self.positions_attempted > 0:
            accuracy = (self.correct_answers / self.positions_attempted) * 100
            avg_time = self.total_time / self.positions_attempted
            
            message = (f"Session ended!\n\n"
                      f"Positions attempted: {self.positions_attempted}\n"
                      f"Correct answers: {self.correct_answers}\n"
                      f"Accuracy: {accuracy:.1f}%\n"
                      f"Average time: {avg_time:.1f}s")
            
            messagebox.showinfo("Session Complete", message)
        
        # Call session end callback if set
        if self.on_session_end:
            self.on_session_end()
    
    def update_stats_display(self):
        """Update the statistics display."""
        if self.positions_attempted > 0:
            accuracy = (self.correct_answers / self.positions_attempted) * 100
            stats_text = f"{self.correct_answers}/{self.positions_attempted} correct ({accuracy:.1f}%)"
        else:
            stats_text = "0/0 correct"
        
        self.stats_label.config(text=stats_text)
    
    def get_session_stats(self):
        """Get current session statistics."""
        return {
            'positions_attempted': self.positions_attempted,
            'correct_answers': self.correct_answers,
            'total_time': self.total_time,
            'accuracy': (self.correct_answers / self.positions_attempted * 100) if self.positions_attempted > 0 else 0,
            'average_time': (self.total_time / self.positions_attempted) if self.positions_attempted > 0 else 0
        } 