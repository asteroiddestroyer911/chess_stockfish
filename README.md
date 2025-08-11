# Chess

A graphical chess game built with Python and Tkinter, featuring integration with the powerful Stockfish chess engine for AI gameplay.

## Features

### Interactive Chess Board: Click-and-play interface with move highlighting and piece selection

### Stockfish AI Integration: Play against the world-class Stockfish chess engine

### Flexible Gameplay: Play human vs human or human vs AI (as White or Black)

### Visual Feedback:

• Legal move highlighting with circles

• Selected piece highlighting

• Check/checkmate/stalemate detection

### Game Controls:

• New game functionality

• Move undo capability

• Board flipping for different perspectives

### Automatic Pawn Promotion: Promotes to Queen by default

### Unicode Chess Pieces: Clean, widely-supported piece symbols

## Requirements

• Python 3.6+

• python-chess library

• tkinter (usually included with Python)

• Stockfish chess engine (for AI gameplay)

## Configuration
You can customize the game by modifying these variables at the top of chess_stockfish.py:

```
STOCKFISH_PATH = shutil.which("stockfish") or "stockfish"  # Path to Stockfish binary
ENGINE_THINK_TIME = 0.1  # AI thinking time in seconds (0.01-5.0)
BOARD_SIZE = 480  # Board size in pixels
LIGHT_COLOR = "#F0D9B5"  # Light square color
DARK_COLOR = "#B58863"   # Dark square color
```
