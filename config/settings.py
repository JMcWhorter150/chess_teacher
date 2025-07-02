import os
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(project_root, '.env'))

CHESS_COM_API_BASE = "https://api.chess.com/pub/"
DATABASE_PATH = "chess_trainer.db"
CHESS_COM_USERNAME = os.getenv("CHESS_COM_USERNAME", "MisoVision")
