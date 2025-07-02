# Chess Training Application Architecture

## 1. Project Overview & Goals

### Purpose
Build a desktop chess training application that helps improve chess skills by analyzing personal games from Chess.com, identifying blunders using Stockfish engine, and providing spaced repetition training on those mistake positions.

### Core Functionality
- **Game Collection**: Fetch user's rapid/blitz games from Chess.com API (last 50 games initially)
- **Blunder Analysis**: Use Stockfish to identify moves with 300+ centipawn evaluation drops
- **Position Training**: Present blunder positions on interactive chess board for user to solve
- **Spaced Repetition**: Schedule position reviews based on performance using spaced repetition algorithm
- **Progress Tracking**: Store all data locally in SQLite database

### Target User Experience
1. User runs application and enters Chess.com username
2. Application fetches and analyzes recent games automatically
3. User practices blunder positions by clicking moves on chess board
4. Application tracks performance and schedules reviews accordingly
5. User builds long-term retention of tactical patterns from their own games

### Technical Stack
- **Language**: Python 3.8+
- **Chess Logic**: python-chess library
- **Engine**: Stockfish (bundled or system-installed)
- **Database**: SQLite3
- **GUI**: Tkinter with PIL for chess board graphics
- **API**: Chess.com public REST API

## 2. File Structure & Architecture

```
chess_trainer/
├── main.py                     # Application entry point, main GUI loop
├── requirements.txt            # Python dependencies
├── README.md                   # Installation and usage instructions
├── config/
│   └── settings.py            # Configuration constants, file paths, API URLs
├── data/
│   ├── database.py            # SQLite database connection and schema
│   └── models.py              # Data classes (Game, Blunder, Review)
├── chess_api/
│   └── chess_com_client.py    # Chess.com API client, game fetching
├── analysis/
│   ├── stockfish_analyzer.py  # Stockfish integration, blunder detection
│   └── position_analyzer.py   # Position evaluation, move comparison
├── gui/
│   ├── main_window.py         # Main application window
│   ├── chess_board.py         # Interactive chess board widget
│   └── training_interface.py  # Training session UI components
├── training/
│   ├── spaced_repetition.py   # Spaced repetition algorithm (SM-2 or similar)
│   └── session_manager.py     # Training session logic, progress tracking
└── utils/
    ├── pgn_parser.py          # PGN parsing utilities
    └── chess_helpers.py       # Chess utility functions
```

### File Responsibilities

**main.py**: Application startup, main window initialization, event loop
**config/settings.py**: Database path, API endpoints, analysis parameters, GUI settings
**data/database.py**: SQLite connection, table creation, CRUD operations
**data/models.py**: Python dataclasses for Game, Blunder, Review objects
**chess_api/chess_com_client.py**: HTTP requests to Chess.com, PGN download
**analysis/stockfish_analyzer.py**: Stockfish process management, position analysis
**analysis/position_analyzer.py**: Move evaluation comparison, blunder identification
**gui/main_window.py**: Main application window, menu system, user interface
**gui/chess_board.py**: Clickable chess board widget, move input handling
**gui/training_interface.py**: Training session display, feedback, progress
**training/spaced_repetition.py**: Review scheduling algorithm, difficulty adjustment
**training/session_manager.py**: Training session coordination, performance tracking
**utils/pgn_parser.py**: PGN string parsing, game extraction
**utils/chess_helpers.py**: Common chess operations, format conversions


## Data Structures & Types

### Key Data Types
- **chess.Board**: Python-chess board state representation
- **chess.Move**: Move representation (from_square, to_square, promotion)
- **str (FEN)**: Forsyth-Edwards Notation for position serialization
- **str (PGN)**: Portable Game Notation for complete game storage
- **int (centipawns)**: Stockfish evaluation units (100 = 1 pawn advantage)
- **datetime**: ISO format strings for scheduling and timestamps

### Database Schema
```sql
CREATE TABLE games (
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

CREATE TABLE blunders (
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

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    blunder_id INTEGER REFERENCES blunders(id),
    last_reviewed TEXT,
    next_review TEXT NOT NULL,
    ease_factor REAL DEFAULT 2.5,
    repetition_count INTEGER DEFAULT 0,
    correct_streak INTEGER DEFAULT 0
);
```
