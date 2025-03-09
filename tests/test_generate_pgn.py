import unittest
import tempfile
import json
import os
import chess.pgn

from src.generate_pgn import calculate_ply_from_fen, generate_pgn

class TestGeneratePGN(unittest.TestCase):

    def test_calculate_ply_from_fen_white(self):
        # White's turn: ply should be 0.
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        ply = calculate_ply_from_fen(fen)
        self.assertEqual(ply, 0)

    def test_calculate_ply_from_fen_black(self):
        # Black's turn: ply should be 1.
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
        ply = calculate_ply_from_fen(fen)
        self.assertEqual(ply, 1)

    def test_calculate_ply_from_fen_invalid(self):
        # An invalid FEN should raise a ValueError.
        with self.assertRaises(ValueError):
            calculate_ply_from_fen("invalid_fen")

    def test_generate_pgn(self):
        # Create sample puzzles: one where it's White's turn and one where it's Black's turn.
        puzzles = [
            {"fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 1"},
            {"fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"}
        ]

        # Create a temporary file for puzzles JSON.
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as puzzle_file:
            json.dump(puzzles, puzzle_file)
            puzzle_file_path = puzzle_file.name

        # Create a temporary file to serve as the output PGN.
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as output_file:
            output_file_path = output_file.name

        try:
            # Generate the PGN from the puzzle JSON.
            generate_pgn(puzzle_file_path, output_pgn=output_file_path)

            # Read the PGN output.
            with open(output_file_path, 'r') as f:
                content = f.read()

            # Verify that the headers include the calculated ply.
            # For the first puzzle, active color is 'w' so ply = (1-1)*2 = 0.
            self.assertIn("Puzzle 1 (Ply 0)", content)
            # For the second puzzle, active color is 'b' so ply = (1-1)*2 + 1 = 1.
            self.assertIn("Puzzle 2 (Ply 1)", content)
            # Also verify that the FEN header is present.
            self.assertIn("FEN", content)
        finally:
            os.remove(puzzle_file_path)
            os.remove(output_file_path)

if __name__ == '__main__':
    unittest.main()
