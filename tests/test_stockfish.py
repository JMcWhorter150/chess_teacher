from stockfish import Stockfish

try:
    stockfish = Stockfish()
    print("Successfully instantiated Stockfish() object.")
except Exception as e:
    print(f"Error instantiating Stockfish() object: {e}")
