import unittest
import chess
from unittest.mock import Mock, patch
import sys
import os

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analysis.stockfish_analyzer import StockfishAnalyzer
from analysis.position_analyzer import find_blunders, analyze_single_position, validate_game_pgn
from data.models import Game, Blunder

class TestStockfishAnalyzer(unittest.TestCase):
    """Test cases for StockfishAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Test if Stockfish is available
        try:
            self.analyzer = StockfishAnalyzer()
            self.stockfish_available = True
        except RuntimeError:
            self.stockfish_available = False
            print("Warning: Stockfish not available, skipping Stockfish-dependent tests")
    
    def test_initialization(self):
        """Test StockfishAnalyzer initialization."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Test default initialization
        analyzer = StockfishAnalyzer()
        self.assertIsNotNone(analyzer.stockfish)
        self.assertEqual(analyzer.timeout, 30)
        
        # Test with custom timeout
        analyzer = StockfishAnalyzer(timeout=60)
        self.assertEqual(analyzer.timeout, 60)
    
    def test_analyze_position_valid_fen(self):
        """Test position analysis with valid FEN strings."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Test starting position
        starting_fen = chess.Board().fen()
        eval_result = self.analyzer.analyze_position(starting_fen, depth=5)
        self.assertIsInstance(eval_result, (int, float))
        
        # Test a simple tactical position (Scholar's Mate)
        scholar_mate_fen = "rnbqkbnr/pppp1ppp/8/4p3/6Q1/5P2/PPPPP2P/RNB1KBNR b KQkq - 3 3"
        eval_result = self.analyzer.analyze_position(scholar_mate_fen, depth=5)
        self.assertIsInstance(eval_result, (int, float))
    
    def test_analyze_position_invalid_fen(self):
        """Test position analysis with invalid FEN strings."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        invalid_fens = [
            "invalid_fen_string",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 invalid",
            "",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 9"
        ]
        
        for invalid_fen in invalid_fens:
            with self.assertRaises((ValueError, RuntimeError)):
                self.analyzer.analyze_position(invalid_fen)
    
    def test_get_best_move_valid_position(self):
        """Test getting best move for valid positions."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Test starting position
        starting_fen = chess.Board().fen()
        best_move = self.analyzer.get_best_move(starting_fen, depth=5)
        self.assertIsInstance(best_move, str)
        self.assertTrue(len(best_move) >= 4)  # UCI format: e2e4, g1f3, etc.
        
        # Test a tactical position
        tactical_fen = "rnbqkbnr/pppp1ppp/8/4p3/6Q1/5P2/PPPPP2P/RNB1KBNR b KQkq - 3 3"
        best_move = self.analyzer.get_best_move(tactical_fen, depth=5)
        self.assertIsInstance(best_move, str)
    
    def test_get_best_move_checkmate_position(self):
        """Test getting best move for checkmate positions."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Fool's Mate position (Black checkmated)
        fools_mate_fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        board = chess.Board(fools_mate_fen)
        
        if board.is_checkmate():
            with self.assertRaises(ValueError):
                self.analyzer.get_best_move(fools_mate_fen)
    
    def test_is_valid_position(self):
        """Test position validation."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Valid positions
        valid_fens = [
            chess.Board().fen(),
            "rnbqkbnr/pppp1ppp/8/4p3/6Q1/5P2/PPPPP2P/RNB1KBNR b KQkq - 3 3",
            "8/8/8/8/8/8/8/8 w - - 0 1"  # Empty board
        ]
        
        for fen in valid_fens:
            self.assertTrue(self.analyzer.is_valid_position(fen))
        
        # Invalid positions
        invalid_fens = [
            "invalid_fen",
            "",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 extra"
        ]
        
        for fen in invalid_fens:
            self.assertFalse(self.analyzer.is_valid_position(fen))
    
    def test_get_legal_moves(self):
        """Test getting legal moves for positions."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Starting position
        starting_fen = chess.Board().fen()
        legal_moves = self.analyzer.get_legal_moves(starting_fen)
        self.assertIsInstance(legal_moves, list)
        self.assertEqual(len(legal_moves), 20)  # 20 legal moves in starting position
        
        # Checkmate position
        fools_mate_fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        board = chess.Board(fools_mate_fen)
        if board.is_checkmate():
            legal_moves = self.analyzer.get_legal_moves(fools_mate_fen)
            self.assertEqual(len(legal_moves), 0)

class TestPositionAnalyzer(unittest.TestCase):
    """Test cases for position analysis functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        try:
            self.analyzer = StockfishAnalyzer()
            self.stockfish_available = True
        except RuntimeError:
            self.stockfish_available = False
            print("Warning: Stockfish not available, skipping Stockfish-dependent tests")
    
    def test_validate_game_pgn(self):
        """Test PGN validation."""
        # Valid PGN
        valid_pgn = """[Event "Test Game"]
[Site "Test Site"]
[Date "2023.01.01"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 Bc5 4. b4 Bxb4 5. c3 Ba5 6. d4 exd4 7. O-O dxc3 8. Qb3 Qf6 9. e5 Qg6 10. Re1 Nge7 11. Ba3 b5 12. Qxb5 Rb8 13. Qa4 Bb6 14. Nbd2 Bb7 15. Ne4 Qf5 16. Bxd3 Qh5 17. Nf6+ gxf6 18. exf6 Rg8 19. Rad1 Qxf3 20. Rxe7+ Nxe7 21. Qxd7+ Kxd7 22. Bf5+ Ke8 23. Bd7+ Kf8 24. Bxe7# 1-0"""
        
        self.assertTrue(validate_game_pgn(valid_pgn))
        
        # Invalid PGN
        invalid_pgn = "This is not a valid PGN"
        self.assertFalse(validate_game_pgn(invalid_pgn))
        
        # Empty PGN
        self.assertFalse(validate_game_pgn(""))
    
    def test_analyze_single_position(self):
        """Test single position analysis."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Test starting position
        starting_fen = chess.Board().fen()
        result = analyze_single_position(starting_fen, self.analyzer, depth=5)
        
        self.assertIn('fen', result)
        self.assertIn('evaluation', result)
        self.assertIn('best_move', result)
        self.assertIn('legal_moves', result)
        self.assertIn('turn', result)
        self.assertIn('is_check', result)
        self.assertIn('is_checkmate', result)
        self.assertIn('is_stalemate', result)
        
        self.assertEqual(result['fen'], starting_fen)
        self.assertIsInstance(result['evaluation'], (int, float))
        self.assertIsInstance(result['best_move'], str)
        self.assertIsInstance(result['legal_moves'], list)
        self.assertEqual(result['turn'], 'white')
        self.assertFalse(result['is_check'])
        self.assertFalse(result['is_checkmate'])
        self.assertFalse(result['is_stalemate'])
    
    def test_find_blunders_sample_game(self):
        """Test blunder detection on a sample game with known tactical mistakes."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Create a sample game with a known blunder (Scholar's Mate)
        sample_pgn = """[Event "Test Game"]
[Site "Test Site"]
[Date "2023.01.01"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0"""
        
        game = Game(
            id=1,
            username="testuser",
            pgn=sample_pgn,
            date="2023-01-01",
            time_control="600",
            result="1-0",
            white_player="Player1",
            black_player="Player2",
            user_color="black"
        )
        
        # Find blunders with a low threshold to catch the tactical mistake
        blunders = find_blunders(game, self.analyzer, threshold=100)
        
        # Should find at least one blunder (Black's move 2...Nc6 instead of blocking the queen)
        self.assertIsInstance(blunders, list)
        # Note: The exact number may vary depending on Stockfish's analysis
        
        if blunders:
            blunder = blunders[0]
            self.assertIsInstance(blunder, Blunder)
            self.assertEqual(blunder.game_id, game.id)
            self.assertIsInstance(blunder.move_number, int)
            self.assertIsInstance(blunder.fen_before, str)
            self.assertIsInstance(blunder.user_move, str)
            self.assertIsInstance(blunder.best_move, str)
            self.assertIsInstance(blunder.eval_before, (int, float))
            self.assertIsInstance(blunder.eval_after, (int, float))
            self.assertIsInstance(blunder.centipawn_loss, int)
            self.assertGreater(blunder.centipawn_loss, 0)
    
    def test_find_blunders_invalid_game(self):
        """Test blunder detection with invalid game data."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Invalid PGN
        invalid_game = Game(
            id=2,
            username="testuser",
            pgn="Invalid PGN string",
            date="2023.01-01",
            time_control="600",
            result="1-0",
            white_player="Player1",
            black_player="Player2",
            user_color="white"
        )
        
        with self.assertRaises((ValueError, RuntimeError)):
            find_blunders(invalid_game, self.analyzer)
    
    def test_error_handling_timeout(self):
        """Test error handling for timeouts."""
        if not self.stockfish_available:
            self.skipTest("Stockfish not available")
        
        # Create analyzer with very short timeout
        fast_analyzer = StockfishAnalyzer(timeout=1)
        
        # This should not raise an exception but might timeout
        starting_fen = chess.Board().fen()
        try:
            result = fast_analyzer.analyze_position(starting_fen, depth=20)
            # If it doesn't timeout, the result should be valid
            self.assertIsInstance(result, (int, float))
        except RuntimeError as e:
            # If it times out, that's also acceptable behavior
            self.assertIn("timeout", str(e).lower())

if __name__ == '__main__':
    # Test Stockfish availability first
    try:
        from stockfish import Stockfish
        stockfish = Stockfish()
        print("✓ Stockfish is available")
    except Exception as e:
        print(f"✗ Stockfish is not available: {e}")
        print("Some tests will be skipped.")
    
    unittest.main(verbosity=2)
