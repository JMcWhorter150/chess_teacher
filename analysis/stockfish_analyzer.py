from stockfish import Stockfish

class StockfishAnalyzer:
    def __init__(self, engine_path: str = None):
        if engine_path:
            self.stockfish = Stockfish(path=engine_path)
        else:
            self.stockfish = Stockfish()

    def analyze_position(self, fen: str, depth: int = 15) -> float:
        """Analyzes a position and returns the evaluation in centipawns.

        Args:
            fen: The FEN string of the position.
            depth: The search depth for Stockfish.

        Returns:
            The evaluation in centipawns (positive for white advantage, negative for black).
        """
        self.stockfish.set_fen_position(fen)
        evaluation = self.stockfish.get_evaluation(depth)
        if evaluation['type'] == 'cp':
            return evaluation['value']
        elif evaluation['type'] == 'mate':
            # Assign a very high/low value for mate to represent it clearly
            return 10000 if evaluation['value'] > 0 else -10000
        return 0

    def get_best_move(self, fen: str, depth: int = 15) -> str:
        """Gets the best move for a given position.

        Args:
            fen: The FEN string of the position.
            depth: The search depth for Stockfish.

        Returns:
            The best move in UCI format.
        """
        self.stockfish.set_fen_position(fen)
        return self.stockfish.get_best_move(depth)
