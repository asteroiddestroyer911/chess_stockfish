import os
import shutil
import threading
import tkinter as tk
from tkinter import messagebox, simpledialog

import chess
import chess.engine

# --- User settings ---
STOCKFISH_PATH = shutil.which("stockfish") or "stockfish"  # change if needed
ENGINE_THINK_TIME = 0.1  # seconds, increase for stronger play
BOARD_SIZE = 480  # pixels
SQUARE_SIZE = BOARD_SIZE // 8
LIGHT_COLOR = "#F0D9B5"
DARK_COLOR = "#B58863"
HIGHLIGHT_COLOR = "#9CDCFF"
SELECT_COLOR = "#FFFB7D"

# Unicode pieces (widely supported fonts)
UNICODE_PIECES = {
    chess.Piece.from_symbol('P'): '♙',
    chess.Piece.from_symbol('N'): '♘',
    chess.Piece.from_symbol('B'): '♗',
    chess.Piece.from_symbol('R'): '♖',
    chess.Piece.from_symbol('Q'): '♕',
    chess.Piece.from_symbol('K'): '♔',
    chess.Piece.from_symbol('p'): '♟',
    chess.Piece.from_symbol('n'): '♞',
    chess.Piece.from_symbol('b'): '♝',
    chess.Piece.from_symbol('r'): '♜',
    chess.Piece.from_symbol('q'): '♛',
    chess.Piece.from_symbol('k'): '♚',
}

# Helper: map square index to (row, col) in 0..7 with 0 at top (rank 8)
def sq_to_rc(square, flip=False):
    row = 7 - chess.square_rank(square)
    col = chess.square_file(square)
    if flip:
        row, col = 7 - row, 7 - col
    return row, col


def rc_to_sq(row, col, flip=False):
    if flip:
        row, col = 7 - row, 7 - col
    rank = 7 - row
    file = col
    return chess.square(file, rank)


class ChessGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Python Chess — Stockfish Integration")
        self.resizable(False, False)

        # Chess objects
        self.board = chess.Board()
        self.flip = False  # flip board for perspective
        self.selected_sq = None
        self.legal_targets = []
        self.move_stack = []  # (move, san)

        # Engine
        self.engine = None
        self.engine_side = None  # chess.WHITE or chess.BLACK or None
        self.engine_think_time = ENGINE_THINK_TIME

        # UI
        self.canvas = tk.Canvas(self, width=BOARD_SIZE, height=BOARD_SIZE)
        self.canvas.grid(row=0, column=0, columnspan=4)
        self.canvas.bind("<Button-1>", self.on_click)

        btn_new = tk.Button(self, text="New Game", command=self.new_game)
        btn_new.grid(row=1, column=0, sticky="ew")
        btn_undo = tk.Button(self, text="Undo", command=self.undo_move)
        btn_undo.grid(row=1, column=1, sticky="ew")
        btn_flip = tk.Button(self, text="Flip Board", command=self.flip_board)
        btn_flip.grid(row=1, column=2, sticky="ew")
        btn_engine = tk.Button(self, text="Play vs Engine", command=self.ask_play_engine)
        btn_engine.grid(row=1, column=3, sticky="ew")

        # Status
        self.status_var = tk.StringVar()
        self.status_var.set("White to move")
        lbl_status = tk.Label(self, textvariable=self.status_var)
        lbl_status.grid(row=2, column=0, columnspan=4, sticky="ew")

        self.draw_board()

        # If user wants engine right away, prompt
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---------- Engine management ----------
    def start_engine(self):
        if self.engine is not None:
            return
        if not STOCKFISH_PATH:
            messagebox.showerror("Engine not found", "Stockfish path is not set.")
            return
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
        except Exception as e:
            messagebox.showerror("Engine error", f"Could not start Stockfish:\n{e}")
            self.engine = None

    def stop_engine(self):
        if self.engine:
            try:
                self.engine.quit()
            except Exception:
                pass
            self.engine = None

    # ---------- Game control ----------
    def new_game(self):
        self.board.reset()
        self.move_stack.clear()
        self.selected_sq = None
        self.legal_targets = []
        self.status_var.set("White to move")
        self.draw_board()
        # If engine playing Black, let it move
        if self.engine_side == chess.WHITE:
            # engine plays White
            self.after(50, self.engine_move_if_needed)

    def undo_move(self):
        if len(self.move_stack) == 0:
            return
        # undo last move (and engine move if exists)
        self.board.pop()
        self.move_stack.pop()
        self.selected_sq = None
        self.legal_targets = []
        self.status_var.set(("White" if self.board.turn == chess.WHITE else "Black") + " to move")
        self.draw_board()

    def flip_board(self):
        self.flip = not self.flip
        self.draw_board()

    def ask_play_engine(self):
        choice = messagebox.askquestion("Play vs Engine", "Do you want to play as White? (No = play as Black)")
        if choice == 'yes':
            self.engine_side = chess.BLACK
        else:
            self.engine_side = chess.WHITE
        time = simpledialog.askfloat("Engine think time", "Engine think time (seconds)", initialvalue=self.engine_think_time, minvalue=0.01, maxvalue=5.0)
        if time is not None:
            self.engine_think_time = float(time)
        self.start_engine()
        # If engine should move first
        if self.engine_side == chess.WHITE and self.board.turn == chess.WHITE:
            self.after(50, self.engine_move_if_needed)

    def on_close(self):
        self.stop_engine()
        self.destroy()

    # ---------- UI drawing ----------
    def draw_board(self):
        self.canvas.delete("all")
        for r in range(8):
            for c in range(8):
                x1 = c * SQUARE_SIZE
                y1 = r * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE
                light = (r + c) % 2 == 0
                color = LIGHT_COLOR if light else DARK_COLOR
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color, tags=f"sq_{r}_{c}")

        # highlights for legal moves
        for t in self.legal_targets:
            row, col = sq_to_rc(t, flip=self.flip)
            x1 = col * SQUARE_SIZE
            y1 = row * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            self.canvas.create_oval(x1 + SQUARE_SIZE*0.25, y1 + SQUARE_SIZE*0.25, x2 - SQUARE_SIZE*0.25, y2 - SQUARE_SIZE*0.25, fill=HIGHLIGHT_COLOR, outline="")

        # selection
        if self.selected_sq is not None:
            row, col = sq_to_rc(self.selected_sq, flip=self.flip)
            x1 = col * SQUARE_SIZE
            y1 = row * SQUARE_SIZE
            x2 = x1 + SQUARE_SIZE
            y2 = y1 + SQUARE_SIZE
            self.canvas.create_rectangle(x1, y1, x2, y2, outline=SELECT_COLOR, width=3)

        # pieces
        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if piece is None:
                continue
            row, col = sq_to_rc(sq, flip=self.flip)
            x = col * SQUARE_SIZE + SQUARE_SIZE // 2
            y = row * SQUARE_SIZE + SQUARE_SIZE // 2
            symbol = UNICODE_PIECES.get(piece, '?')
            # Draw as text
            self.canvas.create_text(x, y, text=symbol, font=("DejaVu Sans", SQUARE_SIZE//2), tags=(f"piece_{sq}"))

        # update status
        if self.board.is_checkmate():
            winner = "White" if self.board.turn == chess.BLACK else "Black"
            self.status_var.set(f"Checkmate — {winner} wins")
        elif self.board.is_stalemate():
            self.status_var.set("Stalemate")
        elif self.board.is_check():
            self.status_var.set(("White" if self.board.turn == chess.WHITE else "Black") + " to move — Check!")
        else:
            self.status_var.set(("White" if self.board.turn == chess.WHITE else "Black") + " to move")

    # ---------- Input handling ----------
    def on_click(self, event):
        col = event.x // SQUARE_SIZE
        row = event.y // SQUARE_SIZE
        if col < 0 or col > 7 or row < 0 or row > 7:
            return
        sq = rc_to_sq(row, col, flip=self.flip)

        # If engine's turn, ignore human input
        if self.engine_side is not None and self.board.turn == self.engine_side:
            return

        piece = self.board.piece_at(sq)
        if self.selected_sq is None:
            # pick up a piece if it belongs to side to move
            if piece is not None and piece.color == self.board.turn:
                self.selected_sq = sq
                self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
                self.draw_board()
        else:
            # attempt to move
            move = chess.Move(self.selected_sq, sq)
            # handle promotions automatically to queen if needed
            if chess.Move(self.selected_sq, sq) in self.board.legal_moves:
                is_promo = self.is_promotion_move(self.selected_sq, sq)
                if is_promo:
                    # promote to queen by default
                    move = chess.Move(self.selected_sq, sq, promotion=chess.QUEEN)
                self.push_move(move)
            else:
                # clicked elsewhere: if clicking another of your pieces, select it
                if piece is not None and piece.color == self.board.turn:
                    self.selected_sq = sq
                    self.legal_targets = [m.to_square for m in self.board.legal_moves if m.from_square == sq]
                else:
                    # clear selection
                    self.selected_sq = None
                    self.legal_targets = []
            self.draw_board()
            # if engine should move now, trigger it
            self.after(50, self.engine_move_if_needed)

    def is_promotion_move(self, from_sq, to_sq):
        piece = self.board.piece_at(from_sq)
        if piece is None or piece.piece_type != chess.PAWN:
            return False
        to_rank = chess.square_rank(to_sq)
        if (piece.color == chess.WHITE and to_rank == 7) or (piece.color == chess.BLACK and to_rank == 0):
            return True
        return False

    def push_move(self, move: chess.Move):
        try:
            self.board.push(move)
            self.move_stack.append((move, self.board.peek()))
            self.selected_sq = None
            self.legal_targets = []
            self.draw_board()
        except Exception as e:
            print("Invalid move attempted:", e)

    # ---------- Engine play ----------
    def engine_move_if_needed(self):
        if self.engine_side is None:
            return
        if self.board.is_game_over():
            return
        if self.board.turn != self.engine_side:
            return
        # make sure engine started
        self.start_engine()
        if not self.engine:
            return

        # run engine in background thread so UI doesn't freeze
        def think_and_move():
            try:
                limit = chess.engine.Limit(time=self.engine_think_time)
                result = self.engine.play(self.board, limit)
                if result is None or result.move is None:
                    return
                self.board.push(result.move)
                self.move_stack.append((result.move, None))
                # redraw on main thread
                self.after(10, self.draw_board)
            except Exception as e:
                print("Engine move error:", e)

        threading.Thread(target=think_and_move, daemon=True).start()


if __name__ == '__main__':
    # check engine availability and warn if missing
    if not STOCKFISH_PATH or not shutil.which(STOCKFISH_PATH):
        # STOCKFISH_PATH might be 'stockfish' but not found; warn user
        print("Warning: Stockfish not found in PATH. To play vs engine, install Stockfish and/or set STOCKFISH_PATH variable in the script to the full path of your binary.")

    app = ChessGUI()
    app.mainloop()
