import chess
from typing import Optional, Callable, Tuple

# Try to import tkinter, but handle the case where it's not available
try:
    import tkinter as tk
    from tkinter import Canvas
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    # Create a mock Canvas class for testing
    class Canvas:
        def __init__(self, *args, **kwargs):
            pass
        def create_rectangle(self, *args, **kwargs):
            return 0
        def create_text(self, *args, **kwargs):
            return 0
        def delete(self, *args, **kwargs):
            pass
        def find_all(self):
            return []
        def type(self, item):
            return "text"
        def bind(self, *args, **kwargs):
            pass

# Try to import PIL, but handle the case where it's not available
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ChessBoardWidget(Canvas):
    """
    Interactive chess board widget that displays a chess position and handles move input.
    """
    
    def __init__(self, parent=None, size=400, **kwargs):
        if TKINTER_AVAILABLE:
            super().__init__(parent, width=size, height=size, **kwargs)
        else:
            # For testing without tkinter, just initialize the mock
            super().__init__()
        
        self.size = size
        self.square_size = size // 8
        self.board = chess.Board()
        self.selected_square = None
        self.legal_moves = []
        self.move_callback = None
        
        # Colors for the board
        self.light_square_color = "#F0D9B5"
        self.dark_square_color = "#B58863"
        self.selected_color = "#7B61FF"
        self.legal_move_color = "#7B61FF"
        
        # Piece images (will be loaded or created)
        self.piece_images = {}
        
        # Bind events only if tkinter is available
        if TKINTER_AVAILABLE:
            self.bind("<Button-1>", self.on_click)
            # Draw the initial board
            self.draw_board()
            self.draw_pieces()
    
    def set_move_callback(self, callback: Callable[[chess.Move], None]):
        """Set callback function to be called when a move is made."""
        self.move_callback = callback
    
    def set_position(self, board: chess.Board):
        """Update the board position and redraw."""
        self.board = board
        self.selected_square = None
        self.legal_moves = []
        self.draw_board()
        self.draw_pieces()
    
    def draw_board(self):
        """Draw the 8x8 chess board grid."""
        if not TKINTER_AVAILABLE:
            return  # Skip drawing if tkinter is not available
            
        for rank in range(8):
            for file in range(8):
                x1 = file * self.square_size
                y1 = (7 - rank) * self.square_size  # Flip rank for display
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Determine square color
                is_light = (rank + file) % 2 == 0
                color = self.light_square_color if is_light else self.dark_square_color
                
                # Draw square
                self.create_rectangle(x1, y1, x2, y2, fill=color, outline="")
    
    def create_piece_symbols(self):
        """Create Unicode chess piece symbols as fallback if images aren't available."""
        piece_symbols = {
            'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
            'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚'
        }
        
        for piece_char, symbol in piece_symbols.items():
            # Create a simple text-based piece representation
            self.piece_images[piece_char] = symbol
    
    def draw_pieces(self):
        """Draw all pieces on the board."""
        if not TKINTER_AVAILABLE:
            return  # Skip drawing if tkinter is not available
            
        # Clear existing pieces
        for item in self.find_all():
            if self.type(item) == "text":
                self.delete(item)
        
        # Create piece symbols if not already done
        if not self.piece_images:
            self.create_piece_symbols()
        
        # Draw each piece
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece is not None:
                self.draw_piece_at_square(square, piece)
    
    def draw_piece_at_square(self, square: chess.Square, piece: chess.Piece):
        """Draw a piece at a specific square."""
        if not TKINTER_AVAILABLE:
            return  # Skip drawing if tkinter is not available
            
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        # Convert to canvas coordinates
        x = file * self.square_size + self.square_size // 2
        y = (7 - rank) * self.square_size + self.square_size // 2
        
        # Get piece symbol
        piece_char = piece.symbol()
        symbol = self.piece_images.get(piece_char, piece_char)
        
        # Determine text color (white pieces on dark squares, black pieces on light squares)
        is_light_square = (rank + file) % 2 == 0
        text_color = "black" if is_light_square else "white"
        
        # Draw piece symbol
        self.create_text(x, y, text=symbol, font=("Arial", self.square_size // 3), 
                        fill=text_color, tags="piece")
    
    def highlight_square(self, square: chess.Square, color: str):
        """Highlight a square with the specified color."""
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        
        x1 = file * self.square_size
        y1 = (7 - rank) * self.square_size
        x2 = x1 + self.square_size
        y2 = y1 + self.square_size
        
        # Create highlight rectangle
        highlight_id = self.create_rectangle(x1, y1, x2, y2, fill=color, 
                                           outline="", stipple="gray50", tags="highlight")
        return highlight_id
    
    def clear_highlights(self):
        """Clear all square highlights."""
        self.delete("highlight")
    
    def pixel_to_square(self, x: int, y: int) -> Optional[chess.Square]:
        """Convert pixel coordinates to chess square."""
        if 0 <= x < self.size and 0 <= y < self.size:
            file = x // self.square_size
            rank = 7 - (y // self.square_size)  # Flip rank back
            if 0 <= file <= 7 and 0 <= rank <= 7:
                return chess.square(file, rank)
        return None
    
    def on_click(self, event):
        """Handle mouse click events on the board."""
        square = self.pixel_to_square(event.x, event.y)
        if square is None:
            return
        
        # Clear previous highlights
        self.clear_highlights()
        
        if self.selected_square is None:
            # First click - select piece
            piece = self.board.piece_at(square)
            if piece is not None:
                # Check if it's the correct player's turn
                if piece.color == self.board.turn:
                    self.selected_square = square
                    self.legal_moves = [move for move in self.board.legal_moves 
                                       if move.from_square == square]
                    
                    # Highlight selected square
                    self.highlight_square(square, self.selected_color)
                    
                    # Highlight legal moves
                    for move in self.legal_moves:
                        self.highlight_square(move.to_square, self.legal_move_color)
        else:
            # Second click - make move
            move = chess.Move(self.selected_square, square)
            
            # Check if it's a legal move
            if move in self.board.legal_moves:
                # Make the move
                self.board.push(move)
                
                # Call callback if set
                if self.move_callback:
                    self.move_callback(move)
                
                # Redraw board
                self.draw_pieces()
            
            # Reset selection
            self.selected_square = None
            self.legal_moves = []
    
    def get_fen(self) -> str:
        """Get the current position in FEN notation."""
        return self.board.fen()
    
    def set_fen(self, fen: str):
        """Set the board position from FEN notation."""
        try:
            self.board = chess.Board(fen)
            self.selected_square = None
            self.legal_moves = []
            self.draw_board()
            self.draw_pieces()
        except ValueError as e:
            print(f"Invalid FEN: {e}")
    
    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.board.is_game_over()
    
    def get_game_result(self) -> Optional[str]:
        """Get the game result if the game is over."""
        if not self.is_game_over():
            return None
        
        if self.board.is_checkmate():
            winner = "black" if self.board.turn else "white"
            return f"Checkmate - {winner} wins"
        elif self.board.is_stalemate():
            return "Stalemate"
        elif self.board.is_insufficient_material():
            return "Draw - insufficient material"
        elif self.board.is_fifty_moves():
            return "Draw - fifty move rule"
        elif self.board.is_repetition():
            return "Draw - repetition"
        else:
            return "Draw" 