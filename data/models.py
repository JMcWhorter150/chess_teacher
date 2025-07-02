from dataclasses import dataclass

@dataclass
class Game:
    id: int
    username: str
    pgn: str
    date: str
    time_control: str
    result: str
    white_player: str
    black_player: str
    user_color: str

@dataclass
class Blunder:
    id: int
    game_id: int
    move_number: int
    fen_before: str
    user_move: str
    best_move: str
    eval_before: float
    eval_after: float
    centipawn_loss: int

@dataclass
class Review:
    id: int
    blunder_id: int
    last_reviewed: str
    next_review: str
    ease_factor: float
    repetition_count: int
    correct_streak: int
