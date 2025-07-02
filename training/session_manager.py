import random
from typing import List, Optional, Callable
from datetime import datetime, date
import logging

from data.models import Blunder, Review
from data.database import create_connection, get_due_reviews, record_attempt
from config.settings import DATABASE_PATH
from .spaced_repetition import SpacedRepetition

logger = logging.getLogger(__name__)

class TrainingSession:
    """
    Manages a training session with blunder positions and spaced repetition logic.
    """
    
    def __init__(self, username: str, max_positions: int = 20, auto_load_positions: bool = True):
        self.username = username
        self.max_positions = max_positions
        self.conn = create_connection(DATABASE_PATH)
        
        # Initialize spaced repetition system
        self.spaced_repetition = SpacedRepetition(username)
        
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
        
        # Load available positions only if auto_load is enabled
        if auto_load_positions:
            self.load_available_positions()
    
    def load_available_positions(self):
        """Load positions that are due for review."""
        if not self.conn:
            return
        
        # Get due reviews using spaced repetition system
        self.available_positions = self.spaced_repetition.get_due_reviews()
        
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
        logger.debug(f"get_next_review_position: current_index={self.current_position_index}, total_positions={len(self.available_positions)}")
        if self.current_position_index >= len(self.available_positions):
            logger.debug("No more positions available")
            return None
        
        position = self.available_positions[self.current_position_index]
        self.current_position_index += 1
        logger.debug(f"Returning position {self.current_position_index-1}: {position[0].id}")
        return position
    
    def has_more_positions(self) -> bool:
        """Check if there are more positions available."""
        return self.current_position_index < len(self.available_positions)
    
    def record_attempt(self, blunder_id: int, correct: bool, time_taken: float, quality: int = None):
        """Record a training attempt and update spaced repetition schedule."""
        if not self.conn:
            return
        
        # Update session statistics
        self.positions_attempted += 1
        if correct:
            self.correct_answers += 1
        self.total_time += time_taken
        
        # Find the review record for this blunder
        review = None
        for blunder, rev in self.available_positions:
            if blunder.id == blunder_id:
                review = rev
                break
        
        if review:
            # Update review using improved spaced repetition algorithm
            if quality is None:
                # Convert correct/incorrect to quality rating
                quality = 5 if correct else 1
            
            if not correct and review.correct_streak == 0 and review.repetition_count > 2:
                # Handle repeated failures with increased spacing
                updated_review = self.spaced_repetition.handle_repeated_failure(review)
            else:
                # Normal spaced repetition update
                updated_review = self.spaced_repetition.calculate_next_review(review, quality)
            
            self.spaced_repetition.update_review(updated_review)
        else:
            # Fallback to old method if review not found
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
        
        # Get additional statistics from spaced repetition system
        sr_stats = self.spaced_repetition.get_review_statistics()
        
        return {
            'total_due': len(self.available_positions),
            'new_positions': new_positions,
            'repeat_positions': repeat_positions,
            'retention_rate': sr_stats.get('retention_rate', 0),
            'average_ease_factor': sr_stats.get('average_ease_factor', 0),
            'total_reviews': sr_stats.get('total_reviews', 0)
        }
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
        if hasattr(self, 'spaced_repetition'):
            self.spaced_repetition.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def debug_session_state(self):
        """Debug method to show current session state."""
        logger.debug("=== Training Session Debug ===")
        logger.debug(f"Username: {self.username}")
        logger.debug(f"Total available positions: {len(self.available_positions)}")
        logger.debug(f"Current position index: {self.current_position_index}")
        logger.debug(f"Positions attempted: {self.positions_attempted}")
        logger.debug(f"Correct answers: {self.correct_answers}")
        
        if self.available_positions:
            logger.debug("Available positions:")
            for i, (blunder, review) in enumerate(self.available_positions):
                logger.debug(f"  {i}: Blunder ID {blunder.id}, Move {blunder.move_number}, Loss {blunder.centipawn_loss}")
        else:
            logger.debug("No available positions")
        logger.debug("================================") 