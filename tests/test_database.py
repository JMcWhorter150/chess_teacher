import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.models import Game
from data.database import create_connection, create_tables, insert_game, get_games_by_username

DB_FILE = "test_chess_trainer.db"

def cleanup_database():
    """Clean up the test database by removing all data"""
    conn = create_connection(DB_FILE)
    if conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM reviews")
        cursor.execute("DELETE FROM blunders")
        cursor.execute("DELETE FROM games")
        conn.commit()
        conn.close()

def test_database():
    # Clean up before running test
    cleanup_database()
    
    conn = create_connection(DB_FILE)
    assert conn is not None

    create_tables(conn)

    # Test insert and get
    game = Game(id=None, username="test_user", pgn="test_pgn", date="2025-07-03", time_control="600", result="1-0", white_player="test_user", black_player="opponent", user_color="white")
    game_id = insert_game(conn, game)
    assert game_id is not None

    games = get_games_by_username(conn, "test_user")
    assert len(games) == 1
    assert games[0].username == "test_user"

    conn.close()

if __name__ == "__main__":
    test_database()
    print("Database tests passed!")
