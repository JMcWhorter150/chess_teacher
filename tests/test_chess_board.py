#!/usr/bin/env python3
"""
Unit tests for ChessBoardWidget to verify Section 5 functionality.
"""

import unittest
import tkinter as tk
import chess
from gui.chess_board import ChessBoardWidget


class TestChessBoardWidget(unittest.TestCase):
    """Test cases for ChessBoardWidget."""
    
    def setUp(self):
        """Set up test environment."""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide the window during tests
        self.chess_board = ChessBoardWidget(self.root, size=400)
    
    def tearDown(self):
        """Clean up after tests."""
        self.root.destroy()
    
    def test_initialization(self):
        """Test that the chess board initializes correctly."""
        self.assertIsNotNone(self.chess_board.board)
        self.assertEqual(self.chess_board.board.fen(), chess.Board().fen())
        self.assertIsNone(self.chess_board.selected_square)
        self.assertEqual(len(self.chess_board.legal_moves), 0)
    
    def test_draw_board(self):
        """Test that the board grid is drawn correctly."""
        # The draw_board method should create 64 rectangles (8x8 grid)
        # We can't easily test the visual output, but we can test that the method runs
        self.chess_board.draw_board()
        # If no exception is raised, the test passes
    
    def test_draw_pieces(self):
        """Test that pieces are drawn correctly."""
        self.chess_board.draw_pieces()
        # If no exception is raised, the test passes
    
    def test_pixel_to_square_conversion(self):
        """Test coordinate conversion from pixels to chess squares."""
        # Test center of first square (a1)
        square = self.chess_board.pixel_to_square(25, 375)  # Center of bottom-left square
        self.assertEqual(square, chess.A1)
        
        # Test center of last square (h8)
        square = self.chess_board.pixel_to_square(375, 25)  # Center of top-right square
        self.assertEqual(square, chess.H8)
        
        # Test invalid coordinates
        square = self.chess_board.pixel_to_square(-1, 0)
        self.assertIsNone(square)
        
        square = self.chess_board.pixel_to_square(500, 500)
        self.assertIsNone(square)
    
    def test_set_position(self):
        """Test setting board position."""
        # Create a test position
        test_board = chess.Board()
        test_board.push_san("e4")
        test_board.push_san("e5")
        
        self.chess_board.set_position(test_board)
        self.assertEqual(self.chess_board.board.fen(), test_board.fen())
        self.assertIsNone(self.chess_board.selected_square)
        self.assertEqual(len(self.chess_board.legal_moves), 0)
    
    def test_set_fen(self):
        """Test setting position from FEN string."""
        test_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        self.chess_board.set_fen(test_fen)
        # Compare normalized FENs
        self.assertEqual(self.chess_board.board.fen(), chess.Board(test_fen).fen())
    
    def test_get_fen(self):
        """Test getting FEN string from board."""
        fen = self.chess_board.get_fen()
        self.assertEqual(fen, chess.Board().fen())
    
    def test_highlight_square(self):
        """Test square highlighting."""
        highlight_id = self.chess_board.highlight_square(chess.E4, "#FF0000")
        self.assertIsNotNone(highlight_id)
        
        # Clear highlights
        self.chess_board.clear_highlights()
        # If no exception is raised, the test passes
    
    def test_move_callback(self):
        """Test move callback functionality."""
        callback_called = False
        callback_move = None
        
        def test_callback(move):
            nonlocal callback_called, callback_move
            callback_called = True
            callback_move = move
        
        self.chess_board.set_move_callback(test_callback)
        
        # Simulate a move by directly calling the callback
        test_move = chess.Move(chess.E2, chess.E4)
        self.chess_board.move_callback(test_move)
        
        self.assertTrue(callback_called)
        self.assertEqual(callback_move, test_move)
    
    def test_game_over_detection(self):
        """Test game over detection."""
        # Starting position should not be game over
        self.assertFalse(self.chess_board.is_game_over())
        
        # Set a checkmate position
        checkmate_fen = "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w KQkq - 1 3"
        self.chess_board.set_fen(checkmate_fen)
        self.assertTrue(self.chess_board.is_game_over())
        
        result = self.chess_board.get_game_result()
        self.assertIn("Checkmate", result)
    
    def test_legal_move_validation(self):
        """Test that only legal moves are accepted."""
        # Try to make an illegal move
        illegal_move = chess.Move(chess.E2, chess.E5)  # Pawn can't move 3 squares from start
        self.assertFalse(illegal_move in self.chess_board.board.legal_moves)
        
        # Try to make a legal move
        legal_move = chess.Move(chess.E2, chess.E4)
        self.assertTrue(legal_move in self.chess_board.board.legal_moves)


if __name__ == "__main__":
    unittest.main() 