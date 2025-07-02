import chess

try:
    board = chess.Board()
    print("Successfully created chess.Board() object.")
except Exception as e:
    print(f"Error creating chess.Board() object: {e}")
