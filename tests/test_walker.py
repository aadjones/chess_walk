from src.walker import generate_and_save_puzzles
from parameters import DIVERGENCE_THRESHOLD
import sys
import unittest
from unittest.mock import patch

import chess

# Add the project root to path
sys.path.append("..")


def fake_get_move_stats(fen, rating):
    """
    Returns legal move lists based on the current board FEN.
    When it's White's turn, returns common white moves.
    When it's Black's turn, returns common black moves.
    """
    board = chess.Board(fen)
    if board.turn:  # White to move
        return ([("e2e4", 0.6), ("g1f3", 0.3), ("d2d4", 0.1)], 100)
    else:  # Black to move
        return ([("e7e5", 0.6), ("g8f6", 0.3), ("d7d5", 0.1)], 100)


class TestWalker(unittest.TestCase):
    def custom_choices_factory(self, moves):
        """
        Returns a custom side_effect function for random.choices that pops moves from
        the provided iterator.
        """
        move_iterator = iter(moves)

        def custom_choices(choices, weights, k):
            # Return the next predetermined move.
            return [next(move_iterator)]

        return custom_choices

    @patch("src.walker.add_puzzle")
    @patch("src.walker.find_divergence")
    @patch("src.walker.random.choices")
    @patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
    def test_generate_and_save_puzzles_success(
        self, mock_get_stats, mock_choices, mock_find_divergence, mock_add_puzzle
    ):
        """
        Test that generate_and_save_puzzles finds and saves a puzzle when a significant divergence is detected.
        """
        # Define a legal move sequence:
        # Ply 1 (White): "e2e4", Ply 2 (Black): "e7e5", Ply 3 (White): "g1f3"
        move_sequence = ["e2e4", "e7e5", "g1f3"]
        mock_choices.side_effect = self.custom_choices_factory(move_sequence)

        # Use a small delta above the threshold.
        delta = 0.01
        divergence_dict = {
            "fen": "fake_fen_after_move",
            "base_freqs": [0.6],
            "target_freqs": [0.6 + DIVERGENCE_THRESHOLD + delta],
        }
        mock_find_divergence.return_value = divergence_dict

        # Use a short walk so that divergence check occurs (min_ply=1, max_ply=3)
        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)

        # Verify that a puzzle was added.
        self.assertTrue(puzzles)
        # The divergence check happens at ply 3.
        mock_add_puzzle.assert_called_with(
            {**divergence_dict, "base_rating": "1600", "target_rating": "2000", "ply": 3}
        )

    @patch("src.walker.get_move_stats", side_effect=lambda fen, rating: ([], 0))
    def test_generate_and_save_puzzles_insufficient_data(self, mock_get_stats):
        """
        Test that generate_and_save_puzzles returns an empty list when there is insufficient move data.
        """
        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)
        self.assertEqual(puzzles, [])

    @patch("src.walker.add_puzzle")
    @patch("src.walker.find_divergence")
    @patch("src.walker.random.choices")
    @patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
    def test_generate_and_save_puzzles_no_significant_divergence(
        self, mock_get_stats, mock_choices, mock_find_divergence, mock_add_puzzle
    ):
        """
        Test that generate_and_save_puzzles does not save puzzles when divergence is detected but below the threshold.
        """
        move_sequence = ["e2e4", "e7e5", "g1f3"]
        mock_choices.side_effect = self.custom_choices_factory(move_sequence)

        # Use a delta below the threshold.
        delta = 0.01
        divergence_dict = {
            "fen": "fake_fen_after_move",
            "base_freqs": [0.6],
            "target_freqs": [0.6 + DIVERGENCE_THRESHOLD - delta],
        }
        mock_find_divergence.return_value = divergence_dict

        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)

        # Expect no puzzles added because the divergence gap is below threshold.
        self.assertEqual(puzzles, [])
        mock_add_puzzle.assert_not_called()


if __name__ == "__main__":
    unittest.main()
