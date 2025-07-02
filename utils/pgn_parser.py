import chess.pgn
from io import StringIO
from data.models import Game

def parse_pgn_string(pgn: str, username: str) -> Game:
    """Parses a PGN string and returns a Game object.

    Args:
        pgn: The PGN of the game.
        username: The username of the user.

    Returns:
        A Game object.
    """
    pgn_io = StringIO(pgn)
    game = chess.pgn.read_game(pgn_io)

    user_color = "white" if game.headers["White"].lower() == username.lower() else "black"

    return Game(
        id=None,
        username=username,
        pgn=pgn,
        date=game.headers.get("Date"),
        time_control=game.headers.get("TimeControl"),
        result=game.headers.get("Result"),
        white_player=game.headers.get("White"),
        black_player=game.headers.get("Black"),
        user_color=user_color,
    )
