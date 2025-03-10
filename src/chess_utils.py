import chess

def get_move_san(board: chess.Board, uci_move: str) -> str:
    """
    Convert a UCI move string (e.g. 'e2e4') into standard algebraic notation (e.g. 'e4').
    If the move is invalid for any reason, fallback to the raw string.
    """
    try:
        move = chess.Move.from_uci(uci_move)
        # Do NOT push to the board unless you want to see captures/check notations, e.g. exd5 or Nf3+
        # board.push(move)  # <--- only if you want to mutate board
        return board.san(move)
    except ValueError:
        # If it's not a valid UCI move for this board position, just return the raw string
        return uci_move