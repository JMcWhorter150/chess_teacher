import chess
import chess.pgn
from typing import List, Optional
from io import StringIO
import logging

from data.models import Game, Blunder
from analysis.stockfish_analyzer import StockfishAnalyzer

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_blunders(game: Game, analyzer: StockfishAnalyzer, threshold: int = 300) -> List[Blunder]:
    """Finds blunders in a given game using Stockfish analysis.

    Args:
        game: The Game object to analyze.
        analyzer: An initialized StockfishAnalyzer instance.
        threshold: The centipawn loss threshold to consider a blunder.

    Returns:
        A list of Blunder objects found in the game.
        
    Raises:
        ValueError: If the game PGN is invalid or cannot be parsed.
        RuntimeError: If Stockfish analysis fails during the process.
    """
    blunders = []
    
    try:
        board = chess.Board()
        game_pgn = chess.pgn.read_game(StringIO(game.pgn))

        # Ensure the game_pgn is not None and has at least one move
        moves = list(game_pgn.mainline_moves()) if game_pgn is not None else []
        if game_pgn is None or not moves:
            raise ValueError(f"Could not parse PGN for game ID {game.id}")

        logger.info(f"Analyzing game {game.id} with {len(moves)} moves")
        
        for i, move in enumerate(moves):
            try:
                # Get position before the move
                fen_before = board.fen()
                
                # Skip analysis if position is invalid
                if not analyzer.is_valid_position(fen_before):
                    logger.warning(f"Invalid position at move {i+1} in game {game.id}, skipping")
                    board.push(move)
                    continue
                
                # Analyze position before move
                eval_before = analyzer.analyze_position(fen_before)
                
                # Make the move
                board.push(move)
                
                # Get position after the move
                fen_after = board.fen()
                
                # Analyze position after move
                eval_after = analyzer.analyze_position(fen_after)

                # Determine whose turn it was before the move to correctly assign blunder
                # Stockfish evaluation is from White's perspective.
                # If it was White's turn, a drop in eval_after means a blunder for White (eval_before - eval_after)
                # If it was Black's turn, a drop in eval_after (more negative) means a blunder for Black (eval_after - eval_before)
                # We want the absolute loss, so we take the absolute difference and then apply the sign based on whose turn it was.

                # If it was White's turn (board.turn is now BLACK, meaning White just moved)
                if board.turn == chess.BLACK:
                    centipawn_loss = eval_before - eval_after
                # If it was Black's turn (board.turn is now WHITE, meaning Black just moved)
                else:
                    centipawn_loss = eval_after - eval_before

                # Check if this move qualifies as a blunder
                if abs(centipawn_loss) > threshold:
                    try:
                        # Get the best move for the position before the blunder
                        best_move = analyzer.get_best_move(fen_before)
                        
                        blunder = Blunder(
                            id=None,
                            game_id=game.id,
                            move_number=i + 1,
                            fen_before=fen_before,
                            user_move=move.uci(),
                            best_move=best_move,
                            eval_before=eval_before,
                            eval_after=eval_after,
                            centipawn_loss=abs(int(centipawn_loss))
                        )
                        
                        blunders.append(blunder)
                        logger.info(f"Found blunder at move {i+1}: {move.uci()} (loss: {abs(int(centipawn_loss))} centipawns)")
                        
                    except (ValueError, RuntimeError) as e:
                        logger.warning(f"Could not get best move for position at move {i+1}: {e}")
                        # Still create the blunder object without the best move
                        blunder = Blunder(
                            id=None,
                            game_id=game.id,
                            move_number=i + 1,
                            fen_before=fen_before,
                            user_move=move.uci(),
                            best_move="",  # Empty string if we couldn't get the best move
                            eval_before=eval_before,
                            eval_after=eval_after,
                            centipawn_loss=abs(int(centipawn_loss))
                        )
                        blunders.append(blunder)
                        
            except (ValueError, RuntimeError) as e:
                logger.error(f"Error analyzing move {i+1} in game {game.id}: {e}")
                # Continue with the next move instead of failing the entire analysis
                try:
                    board.push(move)
                except:
                    logger.error(f"Could not make move {i+1} in game {game.id}, stopping analysis")
                    break

        logger.info(f"Analysis complete for game {game.id}: found {len(blunders)} blunders")
        return blunders
        
    except Exception as e:
        logger.error(f"Failed to analyze game {game.id}: {e}")
        raise RuntimeError(f"Game analysis failed: {e}")

def analyze_single_position(fen: str, analyzer: StockfishAnalyzer, depth: int = 15) -> dict:
    """Analyze a single chess position and return detailed information.
    
    Args:
        fen: The FEN string of the position to analyze.
        analyzer: An initialized StockfishAnalyzer instance.
        depth: The search depth for Stockfish.
        
    Returns:
        Dictionary containing analysis results: evaluation, best move, legal moves, etc.
        
    Raises:
        ValueError: If the FEN string is invalid.
        RuntimeError: If Stockfish analysis fails.
    """
    try:
        # Validate position
        if not analyzer.is_valid_position(fen):
            raise ValueError(f"Invalid FEN string: {fen}")
        
        board = chess.Board(fen)
        
        # Get basic position info
        result = {
            'fen': fen,
            'is_check': board.is_check(),
            'is_checkmate': board.is_checkmate(),
            'is_stalemate': board.is_stalemate(),
            'is_insufficient_material': board.is_insufficient_material(),
            'turn': 'white' if board.turn else 'black',
            'legal_moves': analyzer.get_legal_moves(fen)
        }
        
        # Get Stockfish analysis
        result['evaluation'] = analyzer.analyze_position(fen, depth)
        
        # Get best move if position is not terminal
        if not (board.is_checkmate() or board.is_stalemate()):
            try:
                result['best_move'] = analyzer.get_best_move(fen, depth)
            except ValueError as e:
                result['best_move'] = None
                result['best_move_error'] = str(e)
        else:
            result['best_move'] = None
            
        return result
        
    except Exception as e:
        logger.error(f"Failed to analyze position {fen}: {e}")
        raise

def validate_game_pgn(pgn: str) -> bool:
    """Validate that a PGN string can be parsed into a valid chess game.
    
    Args:
        pgn: The PGN string to validate.
        
    Returns:
        True if the PGN is valid, False otherwise.
    """
    try:
        game = chess.pgn.read_game(StringIO(pgn))
        if game is None:
            return False
        moves = list(game.mainline_moves())
        return len(moves) > 0
    except:
        return False
