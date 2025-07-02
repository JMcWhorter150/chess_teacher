from stockfish import Stockfish
import chess
import time
from typing import Optional

class StockfishAnalyzer:
    def __init__(self, engine_path: str = None, timeout: int = 30):
        """Initialize Stockfish analyzer with error handling.
        
        Args:
            engine_path: Path to Stockfish executable. If None, uses system default.
            timeout: Maximum time in seconds for analysis operations.
        """
        try:
            if engine_path:
                self.stockfish = Stockfish(path=engine_path)
            else:
                self.stockfish = Stockfish()
            
            # Test the engine is working
            self.stockfish.set_fen_position(chess.Board().fen())
            self.timeout = timeout
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Stockfish: {e}. "
                             f"Please ensure Stockfish is installed and accessible.")

    def analyze_position(self, fen: str, depth: int = 15) -> float:
        """Analyzes a position and returns the evaluation in centipawns.

        Args:
            fen: The FEN string of the position.
            depth: The search depth for Stockfish.

        Returns:
            The evaluation in centipawns (positive for white advantage, negative for black).
            
        Raises:
            ValueError: If the FEN string is invalid.
            RuntimeError: If Stockfish analysis fails or times out.
        """
        try:
            # Validate FEN string
            board = chess.Board(fen)
            
            # Set position with timeout handling
            start_time = time.time()
            self.stockfish.set_fen_position(fen)
            
            # Set depth for analysis
            self.stockfish.set_depth(depth)
            
            # Get evaluation with timeout
            evaluation = self.stockfish.get_evaluation()
            
            if time.time() - start_time > self.timeout:
                raise RuntimeError("Analysis timed out")
            
            if evaluation['type'] == 'cp':
                return evaluation['value']
            elif evaluation['type'] == 'mate':
                # Assign a very high/low value for mate to represent it clearly
                return 10000 if evaluation['value'] > 0 else -10000
            return 0
            
        except ValueError:
            raise ValueError(f"Invalid FEN string: {fen}")
        except Exception as e:
            raise RuntimeError(f"Stockfish analysis failed: {e}")

    def get_best_move(self, fen: str, depth: int = 15) -> str:
        """Gets the best move for a given position.

        Args:
            fen: The FEN string of the position.
            depth: The search depth for Stockfish.

        Returns:
            The best move in UCI format.
            
        Raises:
            ValueError: If the FEN string is invalid.
            RuntimeError: If Stockfish analysis fails or times out.
        """
        try:
            # Validate FEN string
            board = chess.Board(fen)
            
            # Check if position is checkmate or stalemate
            if board.is_checkmate():
                raise ValueError("Position is checkmate - no legal moves")
            if board.is_stalemate():
                raise ValueError("Position is stalemate - no legal moves")
            
            # Set position with timeout handling
            start_time = time.time()
            self.stockfish.set_fen_position(fen)
            
            # Set depth for analysis
            self.stockfish.set_depth(depth)
            
            # Get best move with timeout
            best_move = self.stockfish.get_best_move()
            
            if time.time() - start_time > self.timeout:
                raise RuntimeError("Analysis timed out")
            
            return best_move
            
        except ValueError:
            raise ValueError(f"Invalid FEN string: {fen}")
        except Exception as e:
            raise RuntimeError(f"Stockfish analysis failed: {e}")

    def is_valid_position(self, fen: str) -> bool:
        """Check if a FEN string represents a valid chess position.
        
        Args:
            fen: The FEN string to validate.
            
        Returns:
            True if the position is valid, False otherwise.
        """
        try:
            board = chess.Board(fen)
            return True
        except:
            return False

    def get_legal_moves(self, fen: str) -> list:
        """Get all legal moves in a position.
        
        Args:
            fen: The FEN string of the position.
            
        Returns:
            List of legal moves in UCI format.
            
        Raises:
            ValueError: If the FEN string is invalid.
        """
        try:
            board = chess.Board(fen)
            return [move.uci() for move in board.legal_moves]
        except ValueError:
            raise ValueError(f"Invalid FEN string: {fen}")
