import chess
import chess.svg


def uci_to_san(fen: str, uci_move: str) -> str:
    """
    Convert a UCI move to Standard Algebraic Notation (SAN).
    Args:
        fen (str): The FEN of the position.
        uci_move (str): A UCI move string for the base cohort (e.g. "e2e4").

    Returns:
        str: The SAN of the move.
    """
    board = chess.Board(fen)
    try:
        move_obj = chess.Move.from_uci(uci_move)
        if move_obj in board.legal_moves:
            # Compute SAN before pushing the move.
            san = board.san(move_obj)
            return san
    except Exception:
        pass
    return uci_move


def generate_board_svg_with_arrows(fen: str, base_uci: str = None, target_uci: str = None, size: int = 500) -> str:
    """
    Returns an SVG string representing a chess board from the given FEN.
    Optionally draws two arrows:
      - base_uci (red arrow) for the Base Cohort's top move
      - target_uci (blue arrow) for the Target Cohort's top move

    Args:
        fen (str): The FEN of the position.
        base_uci (str): A UCI move string for the base cohort (e.g. "e2e4").
        target_uci (str): A UCI move string for the target cohort (e.g. "c7c5").
        size (int): The size (in pixels) of the rendered board.

    Returns:
        str: An SVG string with the board image and any requested arrows.
    """
    board = chess.Board(fen)
    # Orient the board to the active player
    orientation = chess.WHITE if board.turn else chess.BLACK

    arrows = []
    if base_uci:
        try:
            base_move = chess.Move.from_uci(base_uci)
            # Optionally check if move is legal: if base_move in board.legal_moves: ...
            # Red arrow
            arrows.append(chess.svg.Arrow(base_move.from_square, base_move.to_square, color="#FF0000"))
        except ValueError:
            pass  # If the UCI is invalid, we just skip drawing

    if target_uci:
        try:
            target_move = chess.Move.from_uci(target_uci)
            # Blue arrow
            arrows.append(chess.svg.Arrow(target_move.from_square, target_move.to_square, color="#0000FF"))
        except ValueError:
            pass

    # Generate the SVG with the requested arrows
    svg_code = chess.svg.board(board=board, size=size, orientation=orientation, arrows=arrows)
    return svg_code
