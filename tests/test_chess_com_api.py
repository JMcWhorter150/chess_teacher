import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from chess_api.chess_com_client import get_recent_games
from utils.pgn_parser import parse_pgn_string
from config.settings import CHESS_COM_USERNAME


def test_chess_com_api():
    games = get_recent_games(CHESS_COM_USERNAME, count=5)
    assert len(games) > 0

    for pgn in games:
        game_obj = parse_pgn_string(pgn, CHESS_COM_USERNAME)
        assert game_obj.username == CHESS_COM_USERNAME
        assert game_obj.pgn is not None
        assert game_obj.date is not None
        assert game_obj.white_player is not None
        assert game_obj.black_player is not None

if __name__ == "__main__":
    test_chess_com_api()
    print("Chess.com API tests passed!")
