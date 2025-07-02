from datetime import datetime, date, timedelta
from typing import List, Optional
from data.models import Review
from data.database import create_connection, get_due_reviews, insert_or_update_review
from config.settings import DATABASE_PATH


class SpacedRepetition:
    """
    Implements the SM-2 spaced repetition algorithm for scheduling review intervals.
    
    The SM-2 algorithm adjusts review intervals based on user performance:
    - Quality rating affects ease factor
    - Ease factor determines interval length
    - Intervals increase with successful repetitions
    """
    
    # SM-2 algorithm constants
    INITIAL_EASE_FACTOR = 2.5
    MIN_EASE_FACTOR = 1.3
    MAX_EASE_FACTOR = 2.5
    
    # Initial intervals for new items (in days)
    INITIAL_INTERVALS = [1, 6]
    
    def __init__(self, username: str):
        self.username = username
        self.conn = create_connection(DATABASE_PATH)
    
    def calculate_next_review(self, review: Review, quality: int) -> Review:
        """
        Calculate the next review date based on SM-2 algorithm.
        
        Args:
            review: The current review record
            quality: Quality rating (0-5, where 5 is perfect recall)
        
        Returns:
            Updated review record with new next_review date and ease_factor
        """
        # Update last reviewed timestamp
        review.last_reviewed = datetime.now().isoformat()
        review.repetition_count += 1
        
        # Calculate new ease factor based on quality
        review.ease_factor = self._calculate_ease_factor(review.ease_factor, quality)
        
        # Calculate next interval
        if review.repetition_count == 1:
            # First repetition: use first interval
            interval = self.INITIAL_INTERVALS[0]
        elif review.repetition_count == 2:
            # Second repetition: use second interval
            interval = self.INITIAL_INTERVALS[1]
        else:
            # Subsequent repetitions: multiply previous interval by ease factor
            interval = int(review.repetition_count * review.ease_factor)
        
        # Calculate next review date
        next_review_date = date.today() + timedelta(days=interval)
        review.next_review = next_review_date.isoformat()
        
        # Update correct streak
        if quality >= 4:  # Good or perfect recall
            review.correct_streak += 1
        else:
            review.correct_streak = 0
        
        return review
    
    def _calculate_ease_factor(self, current_ease: float, quality: int) -> float:
        """
        Calculate new ease factor based on quality rating.
        
        The formula is: EF = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
        where q is the quality rating (0-5).
        
        Args:
            current_ease: Current ease factor
            quality: Quality rating (0-5)
        
        Returns:
            New ease factor
        """
        if quality < 0 or quality > 5:
            raise ValueError("Quality must be between 0 and 5")
        
        # SM-2 ease factor calculation
        q_factor = 5 - quality
        ease_change = 0.1 - q_factor * (0.08 + q_factor * 0.02)
        new_ease = current_ease + ease_change
        
        # Apply bounds
        new_ease = max(self.MIN_EASE_FACTOR, min(self.MAX_EASE_FACTOR, new_ease))
        
        return new_ease
    
    def get_due_reviews(self) -> List[tuple]:
        """
        Get all reviews that are due for today or earlier.
        
        Returns:
            List of (blunder, review) tuples that are due for review
        """
        if not self.conn:
            return []
        
        return get_due_reviews(self.conn, self.username)
    
    def reset_difficult_items(self, review: Review) -> Review:
        """
        Reset a difficult item to initial state for repeated failures.
        
        Args:
            review: The review record to reset
        
        Returns:
            Reset review record
        """
        review.ease_factor = self.INITIAL_EASE_FACTOR
        review.repetition_count = 0
        review.correct_streak = 0
        review.next_review = date.today().isoformat()
        
        return review
    
    def get_review_statistics(self) -> dict:
        """
        Get statistics about review performance and scheduling.
        
        Returns:
            Dictionary with review statistics
        """
        if not self.conn:
            return {}
        
        cur = self.conn.cursor()
        
        # Get total reviews
        cur.execute("""
            SELECT COUNT(*) FROM reviews r
            JOIN blunders b ON r.blunder_id = b.id
            JOIN games g ON b.game_id = g.id
            WHERE g.username = ?
        """, (self.username,))
        total_reviews = cur.fetchone()[0]
        
        # Get average ease factor
        cur.execute("""
            SELECT AVG(ease_factor) FROM reviews r
            JOIN blunders b ON r.blunder_id = b.id
            JOIN games g ON b.game_id = g.id
            WHERE g.username = ?
        """, (self.username,))
        avg_ease = cur.fetchone()[0] or 0
        
        # Get due reviews count
        due_reviews = len(self.get_due_reviews())
        
        # Get retention rate (items with correct streak > 0)
        cur.execute("""
            SELECT COUNT(*) FROM reviews r
            JOIN blunders b ON r.blunder_id = b.id
            JOIN games g ON b.game_id = g.id
            WHERE g.username = ? AND r.correct_streak > 0
        """, (self.username,))
        retained_items = cur.fetchone()[0]
        
        retention_rate = (retained_items / total_reviews * 100) if total_reviews > 0 else 0
        
        return {
            'total_reviews': total_reviews,
            'due_reviews': due_reviews,
            'retention_rate': retention_rate,
            'average_ease_factor': round(avg_ease, 2),
            'retained_items': retained_items
        }
    
    def get_review_schedule(self, days_ahead: int = 30) -> dict:
        """
        Get review schedule for the next N days.
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            Dictionary with daily review counts
        """
        if not self.conn:
            return {}
        
        cur = self.conn.cursor()
        schedule = {}
        
        # Get reviews scheduled for each day in the next N days
        for i in range(days_ahead + 1):
            check_date = (date.today() + timedelta(days=i)).isoformat()
            cur.execute("""
                SELECT COUNT(*) FROM reviews r
                JOIN blunders b ON r.blunder_id = b.id
                JOIN games g ON b.game_id = g.id
                WHERE g.username = ? AND r.next_review = ?
            """, (self.username, check_date))
            count = cur.fetchone()[0]
            if count > 0:
                schedule[check_date] = count
        
        return schedule
    
    def update_review(self, review: Review) -> int:
        """
        Save updated review to database.
        
        Args:
            review: The review record to save
        
        Returns:
            Review ID
        """
        if not self.conn:
            return 0
        
        return insert_or_update_review(self.conn, review)
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 