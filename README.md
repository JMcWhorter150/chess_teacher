# Chess Teacher

A desktop chess training application that helps improve chess skills by analyzing personal games from Chess.com, identifying blunders using Stockfish engine, and providing spaced repetition training on those mistake positions.

## Features

- **Game Collection**: Fetch user's rapid/blitz games from Chess.com API
- **Blunder Analysis**: Use Stockfish to identify moves with 300+ centipawn evaluation drops
- **Position Training**: Present blunder positions on interactive chess board for user to solve
- **Spaced Repetition**: Schedule position reviews based on performance
- **Progress Tracking**: Store all data locally in SQLite database

## System Requirements

- Python 3.8 or higher
- **Tkinter support** (required for GUI)
- Stockfish chess engine

## Installation

### Prerequisites

#### Tkinter Support
Tkinter is required for the GUI but is not always included with Python installations:

**macOS (Homebrew):**
```bash
brew install python-tk@3.12
```

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Windows:**
Tkinter is usually included with Python installations from python.org

**Verify tkinter is available:**
```bash
python -c "import tkinter; print('tkinter is available')"
```

#### Stockfish
Install Stockfish chess engine:

**macOS:**
```bash
brew install stockfish
```

**Ubuntu/Debian:**
```bash
sudo apt-get install stockfish
```

**Windows:**
Download from [Stockfish website](https://stockfishchess.org/download/)

### Project Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/chess_teacher.git
cd chess_teacher
```

2. Create and activate virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. (Optional) Check your environment:
```bash
python check_environment.py
```

5. Run the application:
```bash
python main.py
```

## Usage

1. Enter your Chess.com username when prompted
2. The application will fetch and analyze your recent games
3. Practice blunder positions by clicking moves on the chess board
4. Track your progress and review positions based on spaced repetition

## Development

### Running Tests

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run all tests
pytest

# Run specific test file
pytest tests/test_section5_core.py -v
```

### Project Structure

```
chess_teacher/
├── main.py                     # Application entry point
├── gui/                        # GUI components
│   └── chess_board.py         # Interactive chess board widget
├── analysis/                   # Chess analysis
├── data/                       # Database and models
├── chess_api/                  # Chess.com API client
├── training/                   # Training algorithms
└── tests/                      # Test files
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request
