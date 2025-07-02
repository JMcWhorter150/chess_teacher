import random
from typing import List, Optional, Callable
from datetime import datetime, date

from data.models import Blunder, Review
from data.database import create_connection, get_due_reviews, record_attempt
from config.settings import DATABASE_PATH


class TrainingSession:
    """
    Manages a training session with blunder positions and spaced repetition logic.
    """
    
    def __init__(self, username: str, max_positions: int = 20):
        self.username = username
        self.max_positions = max_positions
        self.conn = create_connection(DATABASE_PATH)
        
        # Session state
        self.available_positions: List[tuple[Blunder, Review]] = []
        self.current_position_index = 0
        self.session_start_time = datetime.now()
        
        # Statistics
        self.positions_attempted = 0
        self.correct_answers = 0
        self.total_time = 0.0
        
        # Callbacks
        self.on_position_loaded: Optional[Callable[[Blunder, Review], None]] = None
        self.on_session_complete: Optional[Callable[[dict], None]] = None
        
        # Load available positions
        self.load_available_positions()
    
    def load_available_positions(self):
        """Load positions that are due for review."""
        if not self.conn:
            return
        
        # Get due reviews (positions that need to be reviewed today or earlier)
        self.available_positions = get_due_reviews(self.conn, self.username)
        
        # If no due reviews, get some random blunders for practice
        if not self.available_positions:
            # This would need additional database function to get random blunders
            # For now, we'll just use an empty list
            pass
        
        # Shuffle the positions for variety
        random.shuffle(self.available_positions)
        
        # Limit to max_positions
        self.available_positions = self.available_positions[:self.max_positions]
    
    def get_next_review_position(self) -> Optional[tuple[Blunder, Review]]:
        """Get the next position for review."""
        if self.current_position_index >= len(self.available_positions):
            return None
        
        position = self.available_positions[self.current_position_index]
        self.current_position_index += 1
        return position
    
    def has_more_positions(self) -> bool:
        """Check if there are more positions available."""
        return self.current_position_index < len(self.available_positions)
    
    def record_attempt(self, blunder_id: int, correct: bool, time_taken: float):
        """Record a training attempt and update spaced repetition schedule."""
        if not self.conn:
            return
        
        # Update session statistics
        self.positions_attempted += 1
        if correct:
            self.correct_answers += 1
        self.total_time += time_taken
        
        # Record in database
        record_attempt(self.conn, blunder_id, correct, time_taken)
    
    def get_session_statistics(self) -> dict:
        """Get current session statistics."""
        return {
            'positions_attempted': self.positions_attempted,
            'correct_answers': self.correct_answers,
            'total_time': self.total_time,
            'accuracy': (self.correct_answers / self.positions_attempted * 100) if self.positions_attempted > 0 else 0,
            'average_time': (self.total_time / self.positions_attempted) if self.positions_attempted > 0 else 0,
            'positions_remaining': len(self.available_positions) - self.current_position_index,
            'total_positions': len(self.available_positions)
        }
    
    def get_session_summary(self) -> dict:
        """Get a summary of the completed session."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        
        return {
            'username': self.username,
            'session_start': self.session_start_time.isoformat(),
            'session_duration': session_duration,
            'positions_attempted': self.positions_attempted,
            'correct_answers': self.correct_answers,
            'total_time': self.total_time,
            'accuracy': (self.correct_answers / self.positions_attempted * 100) if self.positions_attempted > 0 else 0,
            'average_time': (self.total_time / self.positions_attempted) if self.positions_attempted > 0 else 0,
            'positions_available': len(self.available_positions)
        }
    
    def start_session(self):
        """Start a new training session."""
        self.session_start_time = datetime.now()
        self.current_position_index = 0
        self.positions_attempted = 0
        self.correct_answers = 0
        self.total_time = 0.0
        
        # Reload available positions
        self.load_available_positions()
    
    def end_session(self):
        """End the current training session."""
        if self.on_session_complete:
            summary = self.get_session_summary()
            self.on_session_complete(summary)
    
    def get_position_progress(self) -> tuple[int, int]:
        """Get current position progress (current, total)."""
        return (self.current_position_index, len(self.available_positions))
    
    def get_difficulty_distribution(self) -> dict:
        """Get distribution of position difficulties based on centipawn loss."""
        if not self.available_positions:
            return {}
        
        difficulties = {
            'easy': 0,      # 300-500 centipawns
            'medium': 0,    # 500-800 centipawns
            'hard': 0       # 800+ centipawns
        }
        
        for blunder, _ in self.available_positions:
            loss = blunder.centipawn_loss
            if loss < 500:
                difficulties['easy'] += 1
            elif loss < 800:
                difficulties['medium'] += 1
            else:
                difficulties['hard'] += 1
        
        return difficulties
    
    def get_review_schedule_info(self) -> dict:
        """Get information about the review schedule."""
        if not self.available_positions:
            return {'total_due': 0, 'new_positions': 0, 'repeat_positions': 0}
        
        new_positions = 0
        repeat_positions = 0
        
        for _, review in self.available_positions:
            if review.repetition_count == 0:
                new_positions += 1
            else:
                repeat_positions += 1
        
        return {
            'total_due': len(self.available_positions),
            'new_positions': new_positions,
            'repeat_positions': repeat_positions
        }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 