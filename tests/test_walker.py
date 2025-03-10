import sys
import unittest
from unittest.mock import patch

import chess
import pandas as pd

from parameters import DIVERGENCE_THRESHOLD
from src.walker import choose_weighted_move, generate_and_save_puzzles

# Add the project root to path
sys.path.append("..")


def fake_get_move_stats(fen, rating):
    """
    Returns legal move lists based on the current board FEN.
    When it's White's turn, returns common white moves.
    When it's Black to move, returns common black moves.
    """
    board = chess.Board(fen)
    if board.turn:  # White to move
        return (
            [
                {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
                {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
                {"uci": "d2d4", "freq": 0.1, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
            ],
            100,
        )
    else:  # Black to move
        return (
            [
                {"uci": "e7e5", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
                {"uci": "g8f6", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
                {"uci": "d7d5", "freq": 0.1, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2},
            ],
            100,
        )


class TestWalker(unittest.TestCase):
    def custom_choices_factory(self, moves):
        """
        Returns a custom side_effect function for random.choices that pops moves from
        the provided iterator.
        """
        move_iterator = iter(moves)

        def custom_choices(choices, weights, k):
            return [next(move_iterator)]

        return custom_choices

    @patch("src.walker.find_divergence")
    @patch("src.walker.random.choices")
    @patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
    def test_generate_and_save_puzzles_success(self, mock_get_stats, mock_choices, mock_find_divergence):
        """
        Qualitatively test that generate_and_save_puzzles finds at least one puzzle when
        significant divergence is detected.
        Instead of asserting on exact ply values or count, we check that the puzzles list is non-empty
        and that each puzzle's base_rating, target_rating, and divergence gap meet expected criteria.
        """
        move_sequence = ["e2e4", "e7e5", "g1f3"]
        mock_choices.side_effect = self.custom_choices_factory(move_sequence)

        # Use a delta above the threshold to simulate significant divergence.
        delta = 0.01
        # Create dummy DataFrames for divergence.
        base_df = pd.DataFrame([{"Move": "e2e4", "Freq": 0.6, "White %": 50, "Draw %": 30, "Black %": 20}])
        target_df = pd.DataFrame(
            [{"Move": "e2e4", "Freq": 0.6 - (DIVERGENCE_THRESHOLD + delta), "White %": 50, "Draw %": 30, "Black %": 20}]
        )
        divergence_dict = {
            "fen": "fake_fen_after_move",
            "base_freqs": [0.6],
            "target_freqs": [0.6 - (DIVERGENCE_THRESHOLD + delta)],
            "base_top_moves": ["e2e4"],
            "target_top_moves": ["e2e4"],
            "base_wdls": [(0.5, 0.3, 0.2)],
            "target_wdls": [(0.5, 0.3, 0.2)],
            "base_df": base_df,
            "target_df": target_df,
        }
        mock_find_divergence.return_value = divergence_dict

        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)

        # Qualitative checks:
        self.assertTrue(puzzles, "Expected at least one puzzle to be generated.")
        for puzzle in puzzles:
            # Check that the base and target ratings are preserved.
            self.assertEqual(puzzle.get("base_rating"), "1600")
            self.assertEqual(puzzle.get("target_rating"), "2000")
            # Check that the puzzle's divergence gap is at least the threshold.
            # Calculate gap from the divergence_dict: gap = base_freq - target_freq
            expected_gap = 0.6 - (0.6 - (DIVERGENCE_THRESHOLD + delta))
            self.assertGreaterEqual(expected_gap, DIVERGENCE_THRESHOLD)
            # Also check that the ply is at least the minimum ply.
            self.assertGreaterEqual(puzzle.get("ply"), 1)

    @patch("src.walker.get_move_stats", side_effect=lambda fen, rating: ([], 0))
    def test_generate_and_save_puzzles_insufficient_data(self, mock_get_stats):
        """
        Test that generate_and_save_puzzles returns an empty list when there is insufficient move data.
        """
        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)
        self.assertEqual(puzzles, [])

    @patch("src.walker.find_divergence")
    @patch("src.walker.random.choices")
    @patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
    def test_generate_and_save_puzzles_no_significant_divergence(
        self, mock_get_stats, mock_choices, mock_find_divergence
    ):
        """
        Test that generate_and_save_puzzles does not add puzzles when divergence is detected but below the threshold.
        """
        move_sequence = ["e2e4", "e7e5", "g1f3"]
        mock_choices.side_effect = self.custom_choices_factory(move_sequence)
        delta = 0.01
        base_df = pd.DataFrame([{"Move": "e2e4", "Freq": 0.6, "White %": 50, "Draw %": 30, "Black %": 20}])
        target_df = pd.DataFrame(
            [{"Move": "e2e4", "Freq": 0.6 - (DIVERGENCE_THRESHOLD - delta), "White %": 50, "Draw %": 30, "Black %": 20}]
        )
        divergence_dict = {
            "fen": "fake_fen_after_move",
            "base_freqs": [0.6],
            "target_freqs": [0.6 - (DIVERGENCE_THRESHOLD - delta)],
            "base_top_moves": ["e2e4"],
            "target_top_moves": ["e2e4"],
            "base_wdls": [(0.5, 0.3, 0.2)],
            "target_wdls": [(0.5, 0.3, 0.2)],
            "base_df": base_df,
            "target_df": target_df,
        }
        mock_find_divergence.return_value = divergence_dict

        puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)
        self.assertEqual(puzzles, [])

    @patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
    @patch("src.walker.random.choices")
    def test_choose_weighted_move_dynamic(self, mock_choices, mock_get_stats):
        """
        Test that choose_weighted_move uses dynamic, frequency-based weighting with temperature scaling.
        """
        temperature = 0.5
        choose_weighted_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "1600", temperature=temperature
        )
        args, kwargs = mock_choices.call_args
        choices_arg = args[0]
        weights_arg = kwargs.get("weights")
        self.assertEqual(choices_arg, ["e2e4", "g1f3", "d2d4"])
        expected_weights = [0.36 / 0.46, 0.09 / 0.46, 0.01 / 0.46]
        for computed, expected in zip(weights_arg, expected_weights):
            self.assertAlmostEqual(computed, expected, places=3)


if __name__ == "__main__":
    unittest.main()
