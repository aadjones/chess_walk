import sys
from typing import Callable
from unittest.mock import patch

import chess
import pandas as pd
import pytest

from src.walker import choose_weighted_move, generate_and_save_puzzles

# Add the project root to path
sys.path.append("..")


def fake_get_move_stats(fen: str, rating: str) -> tuple[list[dict], int]:
    """
    Returns legal move lists based on the current board FEN.
    When it's White to move, returns common white moves.
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


def custom_choices_factory(moves: list[str]) -> Callable[[list[str], list[float], int], list[str]]:
    """
    Returns a custom side_effect function for random.choices that pops moves from
    the provided iterator.
    """
    move_iterator = iter(moves)

    def custom_choices(choices: list[str], weights: list[float], k: int) -> list[str]:
        return [next(move_iterator)]

    return custom_choices


@patch("src.walker.save_puzzle_to_csv", return_value=None)
@patch("src.walker.find_divergence")
@patch("src.walker.random.choices")
@patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
def test_generate_and_save_puzzles_success(mock_get_stats, mock_choices, mock_find_divergence, mock_save):
    """
    Qualitatively test that generate_and_save_puzzles finds at least one puzzle when
    significant divergence is detected.
    """
    move_sequence = ["e2e4", "e7e5", "g1f3"]
    mock_choices.side_effect = custom_choices_factory(move_sequence)

    # Create dummy DataFrames for divergence.
    base_df = pd.DataFrame([{"Move": "e2e4", "Freq": 0.6, "White %": 50, "Draw %": 30, "Black %": 20}])
    target_df = pd.DataFrame([{"Move": "e2e4", "Freq": 0.5, "White %": 50, "Draw %": 30, "Black %": 20}])

    divergence_dict = {
        "fen": "fake_fen_after_move",
        "top_base_move": "e2e4",
        "top_target_move": "e2e4",
        "base_df": base_df,
        "target_df": target_df,
    }
    mock_find_divergence.return_value = divergence_dict

    puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)

    assert puzzles, "Expected at least one puzzle to be generated."
    for puzzle in puzzles:
        assert puzzle.get("base_rating") == "1600"
        assert puzzle.get("target_rating") == "2000"
        # Check that the puzzle's ply is at least 1
        assert puzzle.get("ply") >= 1


@patch("src.walker.get_move_stats", side_effect=lambda fen, rating: ([], 0))
@patch("src.walker.save_puzzle_to_csv", return_value=None)
def test_generate_and_save_puzzles_insufficient_data(mock_get_stats, mock_save):
    """
    Test that generate_and_save_puzzles returns an empty list when there is insufficient move data.
    """
    puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)
    assert puzzles == []


@patch("src.walker.save_puzzle_to_csv", return_value=None)
@patch("src.walker.find_divergence")
@patch("src.walker.random.choices")
@patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
def test_generate_and_save_puzzles_no_significant_divergence(
    mock_get_stats, mock_choices, mock_find_divergence, mock_save
):
    """
    Test that generate_and_save_puzzles returns an empty list when divergence is not detected.
    """
    move_sequence = ["e2e4", "e7e5", "g1f3"]
    mock_choices.side_effect = custom_choices_factory(move_sequence)

    # Simulate no significant divergence by having find_divergence return None.
    mock_find_divergence.return_value = None

    puzzles = generate_and_save_puzzles("1600", "2000", min_ply=1, max_ply=3)
    assert puzzles == []


@patch("src.walker.get_move_stats", side_effect=fake_get_move_stats)
@patch("src.walker.random.choices")
def test_choose_weighted_move_dynamic(mock_choices, mock_get_stats):
    """
    Test that choose_weighted_move uses dynamic, frequency-based weighting with temperature scaling.
    """
    temperature = 0.5
    choose_weighted_move("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1", "1600", temperature=temperature)
    args, kwargs = mock_choices.call_args
    choices_arg = args[0]
    weights_arg = kwargs.get("weights")
    assert choices_arg == ["e2e4", "g1f3", "d2d4"]
    expected_weights = [0.36 / 0.46, 0.09 / 0.46, 0.01 / 0.46]
    for computed, expected in zip(weights_arg, expected_weights):
        assert pytest.approx(computed, rel=1e-3) == expected
