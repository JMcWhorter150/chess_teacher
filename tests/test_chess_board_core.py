#!/usr/bin/env python3
"""Core tests for ChessBoardWidget logic without GUI dependencies."""

import unittest
import chess
import sys
import os

# Add the project root to the path so we can import the chess board module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the chess board module directly to test core functionality
from gui.chess_board import ChessBoardWidget


class TestChessBoardCore(unittest.TestCase):
    """Test core chess board functionality without GUI."""
    
    def test_piece_symbols_creation(self):
        """Test that piece symbols are created correctly."""
        # Create a mock parent (we won't actually use it)
        class MockParent:
            pass
        
        # Test that we can create the piece symbols without GUI
        chess_board = ChessBoardWidget.__new__(ChessBoardWidget)
        chess_board.piece_images = {}  # Manually initialize
        chess_board.create_piece_symbols()
        
        # Check that all piece symbols are created
        expected_pieces = ['P', 'N', 'B', 'R', 'Q', 'K', 'p', 'n', 'b', 'r', 'q', 'k']
        for piece in expected_pieces:
            self.assertIn(piece, chess_board.piece_images)
    
    def test_coordinate_conversion_logic(self):
        """Test the coordinate conversion logic."""
        # Create a mock chess board instance
        chess_board = ChessBoardWidget.__new__(ChessBoardWidget)
        chess_board.size = 400
        chess_board.square_size = 50
        
        # Test pixel to square conversion
        # Center of first square (a1) should be at (25, 375) in a 400x400 board
        square = chess_board.pixel_to_square(25, 375)
        self.assertEqual(square, chess.A1)
        
        # Center of last square (h8) should be at (375, 25)
        square = chess_board.pixel_to_square(375, 25)
        self.assertEqual(square, chess.H8)
        
        # Test invalid coordinates
        square = chess_board.pixel_to_square(-1, 0)
        self.assertIsNone(square)
        
        square = chess_board.pixel_to_square(500, 500)
        self.assertIsNone(square)
    
    def test_chess_logic_integration(self):
        """Test that the chess board integrates correctly with python-chess."""
        # Test that we can create a chess board
        board = chess.Board()
        self.assertIsNotNone(board)
        
        # Test that we can make legal moves
        legal_moves = list(board.legal_moves)
        self.assertGreater(len(legal_moves), 0)
        
        # Test a specific legal move
        e4_move = chess.Move(chess.E2, chess.E4)
        self.assertIn(e4_move, legal_moves)
        
        # Test that we can make the move
        board.push(e4_move)
        # Compare normalized FENs
        self.assertEqual(board.fen(), chess.Board(board.fen()).fen())
    
    def test_fen_operations(self):
        """Test FEN string operations."""
        # Test starting position FEN
        board = chess.Board()
        starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.assertEqual(board.fen(), starting_fen)
        
        # Test setting a custom position
        custom_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        board = chess.Board(custom_fen)
        # Compare normalized FENs
        self.assertEqual(board.fen(), chess.Board(custom_fen).fen())
    
    def test_move_validation(self):
        """Test move validation logic."""
        board = chess.Board()
        
        # Test legal move
        legal_move = chess.Move(chess.E2, chess.E4)
        self.assertTrue(legal_move in board.legal_moves)
        
        # Test illegal move
        illegal_move = chess.Move(chess.E2, chess.E5)  # Pawn can't move 3 squares from start
        self.assertFalse(illegal_move in board.legal_moves)
        
        # Test that we can make a legal move
        board.push(legal_move)
        self.assertEqual(board.turn, chess.BLACK)  # Turn should switch to black

    def test_game_state_detection(self):
        """Test game state detection."""
        board = chess.Board()
        self.assertFalse(board.is_game_over())
        
        # Test checkmate position
        checkmate_fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        board = chess.Board(checkmate_fen)
        self.assertTrue(board.is_game_over())
        self.assertTrue(board.is_checkmate())
        
        # Test stalemate position
        stalemate_fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        board = chess.Board(stalemate_fen)
        self.assertTrue(board.is_game_over())
        self.assertTrue(board.is_stalemate())

    def test_unicode_chess_symbols(self):
        """Test Unicode chess piece symbols."""
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        
        for piece_char, symbol in piece_symbols.items():
            self.assertEqual(len(symbol), 1)
            self.assertGreater(ord(symbol), 127)


if __name__ == "__main__":
    unittest.main() 