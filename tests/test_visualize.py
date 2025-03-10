import os
import tempfile
import unittest

import pandas as pd

from src.visualize import visualize_puzzles


class TestVisualize(unittest.TestCase):
    def test_visualize_no_csv(self):
        """
        If the CSV file doesn't exist, visualize_puzzles should log a warning and not produce an HTML file.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "puzzles.csv")  # File does not exist
            output_html = os.path.join(tmpdir, "output.html")
            visualize_puzzles(csv_path=csv_path, output_html=output_html)
            # Expect that no output HTML is generated.
            self.assertFalse(os.path.exists(output_html), "Output HTML should not be created if CSV is missing.")

    def test_visualize_creates_html(self):
        """
        With a dummy CSV file, visualize_puzzles should produce an HTML file that includes expected content.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            csv_path = os.path.join(tmpdir, "puzzles.csv")
            output_html = os.path.join(tmpdir, "output.html")

            # Create a dummy DataFrame that mimics the multi-index CSV that visualize_puzzles expects.
            df = pd.DataFrame(
                {
                    "FEN": [
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",
                        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR",
                    ],
                    "Rating": ["1400", "1800"],
                    "Ply": [4, 4],
                    "DivergenceGap": [0.2, 0.2],
                    "Move": ["e2e4", "e2e4"],
                    "Games": [100, 100],
                    "White %": [50.0, 50.0],
                    "Draw %": [30.0, 30.0],
                    "Black %": [20.0, 20.0],
                    "Freq": [0.6, 0.4],
                }
            )
            # Create a multi-index for the DataFrame.
            index = pd.MultiIndex.from_tuples([("base", 0, 0), ("target", 0, 0)], names=["Cohort", "Row", "PuzzleIdx"])
            df.index = index
            df.to_csv(csv_path)

            # Run the visualization.
            visualize_puzzles(csv_path=csv_path, output_html=output_html)

            # Check that the output HTML file was created.
            self.assertTrue(os.path.exists(output_html), "Output HTML file should be created.")
            with open(output_html, "r", encoding="utf-8") as f:
                content = f.read()
            # Check for expected keywords/phrases.
            self.assertIn("<html>", content, "Output should contain HTML tags.")
            self.assertIn("Chess Divergence Puzzles", content, "Output should have the expected page title.")
            self.assertIn("chess-board", content, "Output should include the chess board container.")


if __name__ == "__main__":
    unittest.main()
