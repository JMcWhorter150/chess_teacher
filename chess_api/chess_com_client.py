import requests
from datetime import datetime

from config.settings import CHESS_COM_API_BASE

def get_user_games(username: str, year: int = 2025, month: int = 10):
    """Fetches a user's monthly game archives.

    Args:
        username: The Chess.com username.
        year: The year to fetch games from (e.g., 2025). Defaults to the current year.
        month: The month to fetch games from (1-12). Defaults to the current month.

    Returns:
        A list of game URLs for the specified month.
    """
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    url = f"{CHESS_COM_API_BASE}player/{username}/games/{year}/{month:02}"
    try:
        response = requests.get(url, headers={"User-Agent": "chess_trainer/1.0"})
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("games", [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching games for {username}: {e}")
        return []

def get_recent_games(username: str, count: int = 50):
    """Fetches a user's most recent games.

    Args:
        username: The Chess.com username.
        count: The number of recent games to fetch.

    Returns:
        A list of PGN strings.
    """
    game_archives = []
    current_date = datetime.now()
    while_count = 0
    while len(game_archives) < count or while_count >= 10:
        game_archives += get_user_games(username, current_date.year, current_date.month)
        current_date.replace(
            year=current_date.year if current_date.month > 1 else current_date.year - 1,
            month=current_date.month - 1 if current_date.month > 1 else 12,
            day=1
        )
        while_count += 1

    if not game_archives:
        return []

    recent_games = []
    for game_archive in reversed(game_archives):
        if len(recent_games) >= count:
            break
        pgn = game_archive.get('pgn', [])
        if pgn:
            recent_games.append(pgn)

    return recent_games
