import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch
import tempfile
import os

from training.spaced_repetition import SpacedRepetition
from data.models import Review, Blunder, Game
from data.database import create_connection, create_tables, insert_game, insert_blunder


class TestSpacedRepetition:
    """Test cases for the SpacedRepetition class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        # Create temporary database file
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Create connection and tables
        conn = create_connection(db_path)
        create_tables(conn)
        
        yield db_path, conn
        
        # Cleanup
        conn.close()
        os.unlink(db_path)
    
    @pytest.fixture
    def sample_data(self, temp_db):
        """Create sample data for testing."""
        db_path, conn = temp_db
        
        # Create sample game
        game = Game(
            id=0,
            username="testuser",
            pgn="1. e4 e5 2. Nf3 Nc6",
            date="2024-01-01",
            time_control="600",
            result="1-0",
            white_player="testuser",
            black_player="opponent",
            user_color="white"
        )
        game_id = insert_game(conn, game)
        
        # Create sample blunder
        blunder = Blunder(
            id=0,
            game_id=game_id,
            move_number=10,
            fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
            user_move="e5",
            best_move="Nc6",
            eval_before=0.0,
            eval_after=-0.5,
            centipawn_loss=300
        )
        blunder_id = insert_blunder(conn, blunder)
        
        return db_path, conn, game_id, blunder_id
    
    @pytest.fixture
    def spaced_repetition(self, sample_data):
        """Create SpacedRepetition instance with sample data."""
        db_path, conn, game_id, blunder_id = sample_data
        
        # Patch the DATABASE_PATH to use our temp database
        with patch('training.spaced_repetition.DATABASE_PATH', db_path):
            sr = SpacedRepetition("testuser")
            yield sr
            sr.close()
    
    def test_initialization(self, spaced_repetition):
        """Test SpacedRepetition initialization."""
        assert spaced_repetition.username == "testuser"
        assert spaced_repetition.conn is not None
        assert spaced_repetition.INITIAL_EASE_FACTOR == 2.5
        assert spaced_repetition.MIN_EASE_FACTOR == 1.3
        assert spaced_repetition.MAX_EASE_FACTOR == 2.5
    
    def test_calculate_ease_factor(self, spaced_repetition):
        """Test ease factor calculation for different quality ratings."""
        # Test perfect recall (quality 5) - should increase if not at max
        ease = spaced_repetition._calculate_ease_factor(2.0, 5)
        assert ease > 2.0  # Should increase ease factor
        
        # Test perfect recall (quality 5) - should stay at max if already at max
        ease = spaced_repetition._calculate_ease_factor(2.5, 5)
        assert ease == 2.5  # Should stay at maximum
        
        # Test good recall (quality 4) - should stay at max (2.5) according to SM-2
        ease = spaced_repetition._calculate_ease_factor(2.5, 4)
        assert ease == 2.5  # Should stay at maximum
        
        # Test poor recall (quality 2)
        ease = spaced_repetition._calculate_ease_factor(2.5, 2)
        assert ease < 2.5  # Should decrease ease factor
        
        # Test very poor recall (quality 0)
        ease = spaced_repetition._calculate_ease_factor(2.5, 0)
        assert ease < 2.5  # Should decrease ease factor significantly
    
    def test_calculate_ease_factor_bounds(self, spaced_repetition):
        """Test that ease factor stays within bounds."""
        # Test minimum bound - quality 0 should be clamped to MIN_EASE_FACTOR
        ease = spaced_repetition._calculate_ease_factor(1.3, 0)
        assert ease == 1.3  # Should be clamped to minimum
        
        # Test maximum bound - quality 5 should be clamped to MAX_EASE_FACTOR
        ease = spaced_repetition._calculate_ease_factor(2.5, 5)
        assert ease <= 2.5  # Should not exceed maximum
    
    def test_calculate_ease_factor_invalid_quality(self, spaced_repetition):
        """Test that invalid quality ratings raise ValueError."""
        with pytest.raises(ValueError):
            spaced_repetition._calculate_ease_factor(2.5, -1)
        
        with pytest.raises(ValueError):
            spaced_repetition._calculate_ease_factor(2.5, 6)
    
    def test_calculate_next_review_first_repetition(self, spaced_repetition):
        """Test next review calculation for first repetition."""
        review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="",
            next_review="2024-01-01",
            ease_factor=2.5,
            repetition_count=0,
            correct_streak=0
        )
        
        updated_review = spaced_repetition.calculate_next_review(review, 4)
        
        assert updated_review.repetition_count == 1
        assert updated_review.last_reviewed is not None
        assert updated_review.correct_streak == 1
        
        # Should use first interval (1 day)
        expected_date = date.today() + timedelta(days=1)
        assert updated_review.next_review == expected_date.isoformat()
    
    def test_calculate_next_review_second_repetition(self, spaced_repetition):
        """Test next review calculation for second repetition."""
        review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="",
            next_review="2024-01-01",
            ease_factor=2.5,
            repetition_count=1,
            correct_streak=1
        )
        
        updated_review = spaced_repetition.calculate_next_review(review, 4)
        
        assert updated_review.repetition_count == 2
        assert updated_review.correct_streak == 2
        
        # Should use second interval (6 days)
        expected_date = date.today() + timedelta(days=6)
        assert updated_review.next_review == expected_date.isoformat()
    
    def test_calculate_next_review_subsequent_repetitions(self, spaced_repetition):
        """Test next review calculation for subsequent repetitions."""
        review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="",
            next_review="2024-01-01",
            ease_factor=2.0,
            repetition_count=3,
            correct_streak=2
        )
        
        updated_review = spaced_repetition.calculate_next_review(review, 4)
        
        assert updated_review.repetition_count == 4
        assert updated_review.correct_streak == 3
        
        # Should use repetition_count * ease_factor
        expected_interval = int(4 * updated_review.ease_factor)
        expected_date = date.today() + timedelta(days=expected_interval)
        assert updated_review.next_review == expected_date.isoformat()
    
    def test_calculate_next_review_poor_performance(self, spaced_repetition):
        """Test next review calculation for poor performance."""
        review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="",
            next_review="2024-01-01",
            ease_factor=2.5,
            repetition_count=2,
            correct_streak=2
        )
        
        updated_review = spaced_repetition.calculate_next_review(review, 1)
        
        assert updated_review.repetition_count == 3
        assert updated_review.correct_streak == 0  # Reset streak
        assert updated_review.ease_factor < 2.5  # Decreased ease factor
    
    def test_reset_difficult_items(self, spaced_repetition):
        """Test resetting difficult items."""
        review = Review(
            id=1,
            blunder_id=1,
            last_reviewed="2024-01-01",
            next_review="2024-01-15",
            ease_factor=1.5,
            repetition_count=5,
            correct_streak=0
        )
        
        reset_review = spaced_repetition.reset_difficult_items(review)
        
        assert reset_review.ease_factor == 2.5
        assert reset_review.repetition_count == 0
        assert reset_review.correct_streak == 0
        assert reset_review.next_review == date.today().isoformat()
    
    def test_get_due_reviews(self, spaced_repetition, sample_data):
        """Test getting due reviews."""
        db_path, conn, game_id, blunder_id = sample_data
        
        # Create a review that's due today
        review = Review(
            id=0,
            blunder_id=blunder_id,
            last_reviewed="2024-01-01",
            next_review=date.today().isoformat(),
            ease_factor=2.5,
            repetition_count=1,
            correct_streak=1
        )
        
        # Insert the review
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO reviews(blunder_id, last_reviewed, next_review, ease_factor, repetition_count, correct_streak)
            VALUES(?, ?, ?, ?, ?, ?)
        """, (review.blunder_id, review.last_reviewed, review.next_review, 
              review.ease_factor, review.repetition_count, review.correct_streak))
        conn.commit()
        
        # Get due reviews
        due_reviews = spaced_repetition.get_due_reviews()
        
        assert len(due_reviews) >= 1
        # Check that we get blunder and review tuples
        for blunder, review in due_reviews:
            assert isinstance(blunder, Blunder)
            assert isinstance(review, Review)
    
    def test_get_review_statistics(self, spaced_repetition, sample_data):
        """Test getting review statistics."""
        db_path, conn, game_id, blunder_id = sample_data
        
        # Create some review records
        reviews = [
            (blunder_id, "2024-01-01", "2024-01-02", 2.5, 1, 1),
            (blunder_id, "2024-01-02", "2024-01-08", 2.3, 2, 2),
            (blunder_id, "2024-01-03", "2024-01-10", 1.8, 3, 0),
        ]
        
        cur = conn.cursor()
        for review_data in reviews:
            cur.execute("""
                INSERT INTO reviews(blunder_id, last_reviewed, next_review, ease_factor, repetition_count, correct_streak)
                VALUES(?, ?, ?, ?, ?, ?)
            """, review_data)
        conn.commit()
        
        stats = spaced_repetition.get_review_statistics()
        
        assert 'total_reviews' in stats
        assert 'due_reviews' in stats
        assert 'retention_rate' in stats
        assert 'average_ease_factor' in stats
        assert 'retained_items' in stats
        
        assert stats['total_reviews'] == 3
        assert stats['average_ease_factor'] > 0
    
    def test_get_review_schedule(self, spaced_repetition, sample_data):
        """Test getting review schedule."""
        db_path, conn, game_id, blunder_id = sample_data
        
        # Create reviews scheduled for different days
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        next_week = (date.today() + timedelta(days=7)).isoformat()
        
        reviews = [
            (blunder_id, "2024-01-01", tomorrow, 2.5, 1, 1),
            (blunder_id, "2024-01-02", next_week, 2.3, 2, 2),
        ]
        
        cur = conn.cursor()
        for review_data in reviews:
            cur.execute("""
                INSERT INTO reviews(blunder_id, last_reviewed, next_review, ease_factor, repetition_count, correct_streak)
                VALUES(?, ?, ?, ?, ?, ?)
            """, review_data)
        conn.commit()
        
        schedule = spaced_repetition.get_review_schedule(days_ahead=10)
        
        assert tomorrow in schedule
        assert next_week in schedule
        assert schedule[tomorrow] == 1
        assert schedule[next_week] == 1
    
    def test_update_review(self, spaced_repetition, sample_data):
        """Test updating review in database."""
        db_path, conn, game_id, blunder_id = sample_data
        
        # Create a review
        review = Review(
            id=0,
            blunder_id=blunder_id,
            last_reviewed="2024-01-01",
            next_review="2024-01-02",
            ease_factor=2.5,
            repetition_count=1,
            correct_streak=1
        )
        
        # Insert the review
        review_id = spaced_repetition.update_review(review)
        assert review_id > 0
        
        # Update the review
        review.id = review_id
        review.ease_factor = 2.0
        review.next_review = "2024-01-10"
        
        updated_id = spaced_repetition.update_review(review)
        assert updated_id == review_id
    
    def test_context_manager(self, sample_data):
        """Test that SpacedRepetition works as a context manager."""
        db_path, conn, game_id, blunder_id = sample_data
        
        with patch('training.spaced_repetition.DATABASE_PATH', db_path):
            with SpacedRepetition("testuser") as sr:
                assert sr.username == "testuser"
                assert sr.conn is not None
            
            # Connection should be closed after context exit
            assert sr.conn is None


class TestSpacedRepetitionIntegration:
    """Integration tests for spaced repetition with session manager."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        conn = create_connection(db_path)
        create_tables(conn)
        
        yield db_path, conn
        
        conn.close()
        os.unlink(db_path)
    
    @pytest.fixture
    def sample_data(self, temp_db):
        """Create sample data for integration testing."""
        db_path, conn = temp_db
        
        # Create multiple games and blunders
        games = []
        blunders = []
        
        for i in range(3):
            game = Game(
                id=0,
                username="testuser",
                pgn=f"1. e4 e5 2. Nf3 Nc6 {i}",
                date="2024-01-01",
                time_control="600",
                result="1-0",
                white_player="testuser",
                black_player="opponent",
                user_color="white"
            )
            game_id = insert_game(conn, game)
            games.append(game_id)
            
            blunder = Blunder(
                id=0,
                game_id=game_id,
                move_number=10 + i,
                fen_before="rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                user_move="e5",
                best_move="Nc6",
                eval_before=0.0,
                eval_after=-0.5,
                centipawn_loss=300 + i * 100
            )
            blunder_id = insert_blunder(conn, blunder)
            blunders.append(blunder_id)
        
        return db_path, conn, games, blunders
    
    def test_spaced_repetition_with_session_manager(self, sample_data):
        """Test integration between spaced repetition and session manager."""
        db_path, conn, games, blunders = sample_data
        
        with patch('training.spaced_repetition.DATABASE_PATH', db_path):
            with patch('training.session_manager.DATABASE_PATH', db_path):
                from training.session_manager import TrainingSession
                
                # Create training session
                session = TrainingSession("testuser", max_positions=10)
                
                # Check that spaced repetition system is initialized
                assert hasattr(session, 'spaced_repetition')
                assert session.spaced_repetition.username == "testuser"
                
                # Test recording attempts with quality ratings
                session.record_attempt(blunders[0], True, 5.0, quality=5)
                session.record_attempt(blunders[1], False, 3.0, quality=1)
                
                # Check statistics
                stats = session.get_review_schedule_info()
                assert 'retention_rate' in stats
                assert 'average_ease_factor' in stats
                
                session.close()
    
    def test_sm2_algorithm_consistency(self, sample_data):
        """Test that SM-2 algorithm produces consistent results."""
        db_path, conn, games, blunders = sample_data
        
        with patch('training.spaced_repetition.DATABASE_PATH', db_path):
            sr = SpacedRepetition("testuser")
            
            # Create a review
            review = Review(
                id=0,
                blunder_id=blunders[0],
                last_reviewed="",
                next_review="2024-01-01",
                ease_factor=2.5,
                repetition_count=0,
                correct_streak=0
            )
            
            # Simulate a learning sequence
            # First review: perfect recall
            review = sr.calculate_next_review(review, 5)
            assert review.repetition_count == 1
            assert review.ease_factor == 2.5  # Should stay at maximum since starting at 2.5
            assert review.correct_streak == 1
            
            # Second review: good recall
            review = sr.calculate_next_review(review, 4)
            assert review.repetition_count == 2
            assert review.ease_factor == 2.5  # Should stay at maximum
            assert review.correct_streak == 2
            
            # Third review: poor recall
            review = sr.calculate_next_review(review, 2)
            assert review.repetition_count == 3
            assert review.ease_factor < 2.5
            assert review.correct_streak == 0
            
            sr.close() 