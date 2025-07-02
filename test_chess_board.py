#!/usr/bin/env python3
"""
Test script for the ChessBoardWidget to verify Section 5 functionality.
"""

import tkinter as tk
from gui.chess_board import ChessBoardWidget
import chess


def on_move_made(move):
    """Callback function called when a move is made."""
    print(f"Move made: {move.uci()}")
    print(f"Current FEN: {chess_board.get_fen()}")
    
    if chess_board.is_game_over():
        result = chess_board.get_game_result()
        print(f"Game over: {result}")


def main():
    """Main test function."""
    # Create main window
    root = tk.Tk()
    root.title("Chess Board Test - Section 5")
    root.geometry("500x500")
    
    # Create chess board widget
    global chess_board
    chess_board = ChessBoardWidget(root, size=400)
    chess_board.pack(pady=20)
    
    # Set move callback
    chess_board.set_move_callback(on_move_made)
    
    # Add some test buttons
    button_frame = tk.Frame(root)
    button_frame.pack(pady=10)
    
    def reset_board():
        chess_board.set_position(chess.Board())
        print("Board reset to starting position")
    
    def test_fen():
        # Set a test position (fool's mate)
        test_fen = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq g3 0 2"
        chess_board.set_fen(test_fen)
        print(f"Set test position: {test_fen}")
    
    tk.Button(button_frame, text="Reset Board", command=reset_board).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Test FEN", command=test_fen).pack(side=tk.LEFT, padx=5)
    
    # Add instructions
    instructions = tk.Label(root, text="Click on pieces to select them, then click on a destination square to make a move.\n"
                                      "Legal moves will be highlighted in blue.", 
                           wraplength=400, justify=tk.CENTER)
    instructions.pack(pady=10)
    
    print("Chess Board Test Started")
    print("Instructions:")
    print("1. Click on a piece to select it (it will be highlighted)")
    print("2. Click on a destination square to make a move")
    print("3. Legal moves will be highlighted in blue")
    print("4. Use the buttons to test different features")
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 