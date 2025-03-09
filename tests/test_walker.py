from unittest.mock import patch
from src.walker import random_walk
import chess

def test_random_walk():
    mock_moves = [("e2e4", 0.5), ("e7e5", 0.3), ("g1f3", 0.2)]
    with patch("src.walker.get_move_stats") as mock_stats:
        mock_stats.return_value = (mock_moves, 1000)
        fen = random_walk("1400-1600", target_ply=3)
        board = chess.Board(fen)
        assert board.fullmove_number >= 2  # After 3 ply
        assert fen != chess.STARTING_FEN