import sqlite3
from sqlite3 import Error
from .models import Game, Blunder, Review
from datetime import datetime, date, timedelta
from typing import List, Optional

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
        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT NOT NULL
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

def get_blunders_by_username(conn, username: str) -> List[Blunder]:
    """Get all blunders for a specific username."""
    cur = conn.cursor()
    cur.execute("""
        SELECT b.* FROM blunders b
        JOIN games g ON b.game_id = g.id
        WHERE g.username = ?
        ORDER BY b.centipawn_loss DESC
    """, (username,))
    
    rows = cur.fetchall()
    blunders = []
    for row in rows:
        # Convert float values to integers for integer fields
        converted_row = list(row)
        converted_row[0] = int(converted_row[0])  # id
        converted_row[1] = int(converted_row[1])  # game_id
        converted_row[2] = int(converted_row[2])  # move_number
        converted_row[8] = int(converted_row[8])  # centipawn_loss
        blunders.append(Blunder(*converted_row))
    return blunders

def get_review_by_blunder_id(conn, blunder_id: int) -> Optional[Review]:
    """Get review record for a specific blunder."""
    cur = conn.cursor()
    cur.execute("SELECT * FROM reviews WHERE blunder_id = ?", (blunder_id,))
    
    row = cur.fetchone()
    if row:
        return Review(*row)
    return None

def get_due_reviews(conn, username: str) -> List[tuple[Blunder, Review]]:
    """Get all blunders with reviews that are due for today or earlier."""
    today = date.today().isoformat()
    cur = conn.cursor()
    cur.execute("""
        SELECT b.*, r.* FROM blunders b
        JOIN games g ON b.game_id = g.id
        LEFT JOIN reviews r ON b.id = r.blunder_id
        WHERE g.username = ? AND (r.next_review <= ? OR r.id IS NULL)
        ORDER BY COALESCE(r.next_review, '1900-01-01')
    """, (username, today))
    
    rows = cur.fetchall()
    results = []
    for row in rows:
        blunder = Blunder(*row[:9])  # First 9 columns are blunder fields
        if row[9] is not None:  # Review exists
            review = Review(*row[9:])  # Remaining columns are review fields
        else:
            # Create a new review record
            review = Review(
                id=0,
                blunder_id=blunder.id,
                last_reviewed="",
                next_review=today,
                ease_factor=2.5,
                repetition_count=0,
                correct_streak=0
            )
        results.append((blunder, review))
    return results

def insert_or_update_review(conn, review: Review):
    """Insert a new review or update an existing one."""
    if review.id == 0:
        # Insert new review
        sql = ''' INSERT INTO reviews(blunder_id, last_reviewed, next_review, ease_factor, repetition_count, correct_streak)
                  VALUES(?,?,?,?,?,?) '''
        cur = conn.cursor()
        cur.execute(sql, (review.blunder_id, review.last_reviewed, review.next_review, 
                         review.ease_factor, review.repetition_count, review.correct_streak))
        conn.commit()
        return cur.lastrowid
    else:
        # Update existing review
        sql = ''' UPDATE reviews 
                  SET last_reviewed=?, next_review=?, ease_factor=?, repetition_count=?, correct_streak=?
                  WHERE id=? '''
        cur = conn.cursor()
        cur.execute(sql, (review.last_reviewed, review.next_review, review.ease_factor,
                         review.repetition_count, review.correct_streak, review.id))
        conn.commit()
        return review.id

def record_attempt(conn, blunder_id: int, correct: bool, time_taken: float):
    """Record a training attempt for a blunder."""
    # Get or create review record
    review = get_review_by_blunder_id(conn, blunder_id)
    if not review:
        review = Review(
            id=0,
            blunder_id=blunder_id,
            last_reviewed="",
            next_review=date.today().isoformat(),
            ease_factor=2.5,
            repetition_count=0,
            correct_streak=0
        )
    
    # Update review based on performance
    review.last_reviewed = datetime.now().isoformat()
    review.repetition_count += 1
    
    if correct:
        review.correct_streak += 1
        # Increase ease factor slightly for correct answers
        review.ease_factor = min(2.5, review.ease_factor + 0.1)
    else:
        review.correct_streak = 0
        # Decrease ease factor for incorrect answers
        review.ease_factor = max(1.3, review.ease_factor - 0.2)
    
    # Calculate next review date (simple spaced repetition)
    if review.repetition_count == 1:
        # First review: 1 day
        days_interval = 1
    elif review.repetition_count == 2:
        # Second review: 6 days
        days_interval = 6
    else:
        # Subsequent reviews: multiply by ease factor
        days_interval = int(review.repetition_count * review.ease_factor)
    
    next_review_date = date.today() + timedelta(days=days_interval)
    review.next_review = next_review_date.isoformat()
    
    # Save the updated review
    return insert_or_update_review(conn, review)

def get_setting(conn, key: str, default: str = None) -> str:
    """Get a setting value from the database."""
    cur = conn.cursor()
    cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
    result = cur.fetchone()
    return result[0] if result else default

def set_setting(conn, key: str, value: str):
    """Set a setting value in the database."""
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
    """, (key, value, datetime.now().isoformat()))
    conn.commit()

def get_all_settings(conn) -> dict:
    """Get all settings from the database."""
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM settings")
    results = cur.fetchall()
    return {row[0]: row[1] for row in results}

def delete_setting(conn, key: str):
    """Delete a setting from the database."""
    cur = conn.cursor()
    cur.execute("DELETE FROM settings WHERE key = ?", (key,))
    conn.commit()

class SettingsManager:
    """Manages application settings stored in the database."""
    
    def __init__(self, conn):
        self.conn = conn
    
    def get_username(self) -> str:
        """Get the current username setting."""
        return get_setting(self.conn, 'username')
    
    def set_username(self, username: str):
        """Set the username setting."""
        set_setting(self.conn, 'username', username)
    
    def get_blunder_threshold(self) -> int:
        """Get the blunder threshold setting."""
        value = get_setting(self.conn, 'blunder_threshold', '300')
        return int(value)
    
    def set_blunder_threshold(self, threshold: int):
        """Set the blunder threshold setting."""
        set_setting(self.conn, 'blunder_threshold', str(threshold))
    
    def get_analysis_depth(self) -> int:
        """Get the analysis depth setting."""
        value = get_setting(self.conn, 'analysis_depth', '15')
        return int(value)
    
    def set_analysis_depth(self, depth: int):
        """Set the analysis depth setting."""
        set_setting(self.conn, 'analysis_depth', str(depth))
    
    def get_max_positions(self) -> int:
        """Get the max positions per session setting."""
        value = get_setting(self.conn, 'max_positions', '20')
        return int(value)
    
    def set_max_positions(self, max_positions: int):
        """Set the max positions per session setting."""
        set_setting(self.conn, 'max_positions', str(max_positions))
    
    def get_all_settings(self) -> dict:
        """Get all settings as a dictionary."""
        return get_all_settings(self.conn)
    
    def reset_to_defaults(self):
        """Reset all settings to their default values."""
        defaults = {
            'blunder_threshold': '300',
            'analysis_depth': '15',
            'max_positions': '20'
        }
        for key, value in defaults.items():
            set_setting(self.conn, key, value)
