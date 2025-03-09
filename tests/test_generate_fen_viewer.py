import unittest
import tempfile
import json
import os
import chess

from src.generate_fen_viewer import (
    calculate_ply_from_fen,
    get_active_color_from_fen,
    convert_coordinate_to_algebraic,
    generate_fen_viewer
)

class TestFENViewer(unittest.TestCase):

    def test_calculate_ply_from_fen_white(self):
        # For a white-to-move position, ply should be (fullmove-1)*2
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ply = calculate_ply_from_fen(fen)
        self.assertEqual(ply, 0)

    def test_calculate_ply_from_fen_black(self):
        # For a black-to-move position, ply should be (fullmove-1)*2+1
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        ply = calculate_ply_from_fen(fen)
        self.assertEqual(ply, 1)

    def test_get_active_color_from_fen(self):
        fen_white = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.assertEqual(get_active_color_from_fen(fen_white), "w")
        fen_black = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        self.assertEqual(get_active_color_from_fen(fen_black), "b")

    def test_convert_coordinate_to_algebraic_legal(self):
        # For a legal move from starting position, e.g., e2e4 should be displayed as "e4"
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        san = convert_coordinate_to_algebraic(fen, "e2e4")
        self.assertEqual(san, "e4")

    def test_convert_coordinate_to_algebraic_illegal(self):
        # For an illegal move (e.g., e2e5 in the starting position), the function should fall back
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        san = convert_coordinate_to_algebraic(fen, "e2e5")
        self.assertEqual(san, "e2e5")

    def test_generate_fen_viewer(self):
        # Create sample puzzles: one where active color is white, one where it's black.
        puzzles = [
            {
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1",
                "base_top_moves": ["e2e4", "d2d4"],
                "base_freqs": [0.6, 0.3],
                "target_top_moves": ["e2e4", "d2d4"],
                "target_freqs": [0.5, 0.4]
            },
            {
                "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1",
                "base_top_moves": ["e7e5", "d7d5"],
                "base_freqs": [0.7, 0.2],
                "target_top_moves": ["e7e5", "d7d5"],
                "target_freqs": [0.6, 0.3],
                "base_rating": "1400",
                "target_rating": "1800"
            }
        ]

        # Create a temporary puzzles JSON file.
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_input:
            json.dump(puzzles, tmp_input)
            tmp_input_path = tmp_input.name

        # Create a temporary output HTML file.
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp_output:
            tmp_output_path = tmp_output.name

        try:
            generate_fen_viewer(tmp_input_path, output_html=tmp_output_path)
            with open(tmp_output_path, "r") as f:
                content = f.read()
            # For the first puzzle, active color is 'w' so ply = 0.
            self.assertIn("Puzzle 1 (Ply 0)", content)
            # For the second puzzle, active color is 'b' so ply = 1.
            self.assertIn("Puzzle 2 (Ply 1)", content)
            # Verify that one of the FEN strings appears in the output.
            self.assertIn("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR", content)
        finally:
            os.remove(tmp_input_path)
            os.remove(tmp_output_path)

if __name__ == '__main__':
    unittest.main()
