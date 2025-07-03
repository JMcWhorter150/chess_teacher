import unittest
import chess
from unittest.mock import Mock, patch
import sys
import os
import tkinter as tk

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data.models import Blunder, Review
from training.session_manager import TrainingSession


class TestTrainingInterface(unittest.TestCase):
    """Test the training interface components."""
    
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the main window
        # Create a mock blunder for testing
        self.test_blunder = Blunder(
            id=1,
            game_id=1,
            move_number=10,
            fen_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            user_move="e2e4",
            best_move="e2e4",
            eval_before=0.0,
            eval_after=0.0,
            centipawn_loss=300
        )
        
        self.test_review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="2024-01-01T10:00:00",
            next_review="2024-01-02T10:00:00",
            ease_factor=2.5,
            repetition_count=1,
            correct_streak=0
        )
    
    def tearDown(self):
        self.root.destroy()
    
    def test_training_screen_initialization(self):
        from gui.training_interface import TrainingScreen
        training_screen = TrainingScreen(self.root)
        self.assertIsNone(training_screen.current_blunder)
        self.assertIsNone(training_screen.current_review)
        self.assertEqual(training_screen.positions_attempted, 0)
        self.assertEqual(training_screen.correct_answers, 0)
    
    def test_load_training_position(self):
        from gui.training_interface import TrainingScreen
        training_screen = TrainingScreen(self.root)
        training_screen.load_training_position(self.test_blunder, self.test_review)
        self.assertEqual(training_screen.current_blunder, self.test_blunder)
        self.assertEqual(training_screen.current_review, self.test_review)
        self.assertIsNotNone(training_screen.start_time)
        self.assertFalse(training_screen.move_made)
    
    def test_move_validation_correct(self):
        from gui.training_interface import TrainingScreen
        training_screen = TrainingScreen(self.root)
        training_screen.load_training_position(self.test_blunder, self.test_review)
        correct_move = chess.Move.from_uci("e2e4")
        training_screen.on_move_made(correct_move)
        self.assertTrue(training_screen.correct_answer)
        self.assertEqual(training_screen.positions_attempted, 1)
        self.assertEqual(training_screen.correct_answers, 1)
    
    def test_move_validation_incorrect(self):
        from gui.training_interface import TrainingScreen
        training_screen = TrainingScreen(self.root)
        training_screen.load_training_position(self.test_blunder, self.test_review)
        incorrect_move = chess.Move.from_uci("e2e3")
        training_screen.on_move_made(incorrect_move)
        self.assertFalse(training_screen.correct_answer)
        self.assertEqual(training_screen.positions_attempted, 1)
        self.assertEqual(training_screen.correct_answers, 0)
    
    def test_session_statistics(self):
        from gui.training_interface import TrainingScreen
        training_screen = TrainingScreen(self.root)
        training_screen.positions_attempted = 10
        training_screen.correct_answers = 7
        training_screen.total_time = 50.0
        stats = training_screen.get_session_stats()
        self.assertEqual(stats['positions_attempted'], 10)
        self.assertEqual(stats['correct_answers'], 7)
        self.assertEqual(stats['accuracy'], 70.0)
        self.assertEqual(stats['average_time'], 5.0)


class TestTrainingSession(unittest.TestCase):
    """Test the training session manager."""
    
    @patch('training.session_manager.create_connection')
    @patch('training.session_manager.get_due_reviews')
    def test_session_initialization(self, mock_get_reviews, mock_create_conn):
        """Test that TrainingSession can be initialized."""
        # Mock database connection
        mock_conn = Mock()
        mock_create_conn.return_value = mock_conn
        
        # Mock empty reviews list
        mock_get_reviews.return_value = []
        
        # Create session
        session = TrainingSession("testuser")
        
        # Verify initialization
        self.assertEqual(session.username, "testuser")
        self.assertEqual(session.max_positions, 20)
        self.assertEqual(len(session.available_positions), 0)
    
    @patch('training.session_manager.create_connection')
    @patch('training.session_manager.get_due_reviews')
    def test_get_next_position(self, mock_get_reviews, mock_create_conn):
        """Test getting the next position for review."""
        # Mock database connection
        mock_conn = Mock()
        mock_create_conn.return_value = mock_conn
        
        # Create test blunder and review
        test_blunder = Blunder(
            id=1, game_id=1, move_number=10,
            fen_before="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            user_move="e2e4", best_move="e2e4",
            eval_before=0.0, eval_after=0.0, centipawn_loss=300
        )
        test_review = Review(
            id=1, blunder_id=1, last_reviewed="2024-01-01T10:00:00",
            next_review="2024-01-02T10:00:00", ease_factor=2.5,
            repetition_count=1, correct_streak=0
        )
        
        # Mock reviews list with one position
        mock_get_reviews.return_value = [(test_blunder, test_review)]
        
        # Create session with auto_load_positions=True (default)
        session = TrainingSession("testuser", auto_load_positions=True)
        
        # Verify that positions were loaded
        self.assertEqual(len(session.available_positions), 1)
        
        # Get next position
        position = session.get_next_review_position()
        
        # Verify position is returned
        self.assertIsNotNone(position)
        self.assertEqual(position[0], test_blunder)
        self.assertEqual(position[1], test_review)
        
        # Verify no more positions
        self.assertFalse(session.has_more_positions())
    
    def test_session_statistics(self):
        with patch('training.session_manager.create_connection') as mock_create_conn:
            with patch('training.session_manager.get_due_reviews') as mock_get_reviews:
                mock_conn = Mock()
                mock_create_conn.return_value = mock_conn
                mock_get_reviews.return_value = []
                session = TrainingSession("testuser")
                session.positions_attempted = 5
                session.correct_answers = 3
                session.total_time = 25.0
                stats = session.get_session_statistics()
                self.assertEqual(stats['positions_attempted'], 5)
                self.assertEqual(stats['correct_answers'], 3)
                self.assertEqual(stats['accuracy'], 60.0)
                self.assertEqual(stats['average_time'], 5.0)


if __name__ == '__main__':
    unittest.main() 