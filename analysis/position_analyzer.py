import chess
from typing import List
from io import StringIO

from data.models import Game, Blunder
from analysis.stockfish_analyzer import StockfishAnalyzer

def find_blunders(game: Game, analyzer: StockfishAnalyzer, threshold: int = 300) -> List[Blunder]:
    """Finds blunders in a given game using Stockfish analysis.

    Args:
        game: The Game object to analyze.
        analyzer: An initialized StockfishAnalyzer instance.
        threshold: The centipawn loss threshold to consider a blunder.

    Returns:
        A list of Blunder objects found in the game.
    """
    blunders = []
    board = chess.Board()
    game_pgn = chess.pgn.read_game(StringIO(game.pgn))

    # Ensure the game_pgn is not None before proceeding
    if game_pgn is None:
        print(f"Warning: Could not parse PGN for game ID {game.id}. Skipping blunder analysis.")
        return []

    for i, move in enumerate(game_pgn.mainline_moves()):
        fen_before = board.fen()
        eval_before = analyzer.analyze_position(fen_before)

        board.push(move)

        fen_after = board.fen()
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

        if abs(centipawn_loss) > threshold:
            blunders.append(Blunder(
                id=None,
                game_id=game.id,
                move_number=i + 1,
                fen_before=fen_before,
                user_move=move.uci(),
                best_move=analyzer.get_best_move(fen_before),
                eval_before=eval_before,
                eval_after=eval_after,
                centipawn_loss=abs(int(centipawn_loss))
            ))

    return blunders
