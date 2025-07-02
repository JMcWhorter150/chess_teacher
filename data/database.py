import sqlite3
from sqlite3 import Error
from .models import Game, Blunder, Review

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return conn

def create_tables(conn):
    """ create tables in the SQLite database
    :param conn: Connection object
    """
    try:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                pgn TEXT NOT NULL,
                date TEXT NOT NULL,
                time_control TEXT,
                result TEXT,
                white_player TEXT,
                black_player TEXT,
                user_color TEXT
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS blunders (
                id INTEGER PRIMARY KEY,
                game_id INTEGER REFERENCES games(id),
                move_number INTEGER,
                fen_before TEXT NOT NULL,
                user_move TEXT NOT NULL,
                best_move TEXT NOT NULL,
                eval_before REAL,
                eval_after REAL,
                centipawn_loss INTEGER
            );
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY,
                blunder_id INTEGER REFERENCES blunders(id),
                last_reviewed TEXT,
                next_review TEXT NOT NULL,
                ease_factor REAL DEFAULT 2.5,
                repetition_count INTEGER DEFAULT 0,
                correct_streak INTEGER DEFAULT 0
            );
        """)
    except Error as e:
        print(e)

def insert_game(conn, game: Game):
    sql = ''' INSERT INTO games(username,pgn,date,time_control,result,white_player,black_player,user_color)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (game.username, game.pgn, game.date, game.time_control, game.result, game.white_player, game.black_player, game.user_color))
    conn.commit()
    return cur.lastrowid

def insert_blunder(conn, blunder: Blunder):
    sql = ''' INSERT INTO blunders(game_id,move_number,fen_before,user_move,best_move,eval_before,eval_after,centipawn_loss)
              VALUES(?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, (blunder.game_id, blunder.move_number, blunder.fen_before, blunder.user_move, blunder.best_move, blunder.eval_before, blunder.eval_after, blunder.centipawn_loss))
    conn.commit()
    return cur.lastrowid

def get_games_by_username(conn, username: str):
    cur = conn.cursor()
    cur.execute("SELECT * FROM games WHERE username=?", (username,))

    rows = cur.fetchall()

    games = []
    for row in rows:
        games.append(Game(*row))
    return games
