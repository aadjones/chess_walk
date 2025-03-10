import sys
from unittest.mock import patch
import pandas as pd
from parameters import DIVERGENCE_THRESHOLD, MIN_GAMES
from src.divergence import find_divergence

sys.path.append("..")  # Add parent directory to path

# Updated default move lists with "games_total"
DEFAULT_BASE_MOVES = [
    {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
    {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
]
DEFAULT_TARGET_MOVES = [
    {"uci": "g1f3", "freq": 0.8, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
    {"uci": "e2e4", "freq": 0.1, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
]


def test_find_divergence():
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, 1000), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is not None
        # Check that the top base move in the DataFrame is e2e4
        top_base_move = result["base_df"].iloc[0]["Move"]
        top_target_move = result["target_df"].iloc[0]["Move"]
        assert top_base_move == "e2e4"
        assert top_target_move == "g1f3"
        # Calculate the frequency difference for the top base move
        base_freq = result["base_df"].iloc[0]["Freq"]
        target_freq_of_base_move = result["target_df"][result["target_df"]["Move"] == top_base_move]["Freq"]
        target_freq_of_base_move = target_freq_of_base_move.iloc[0] if not target_freq_of_base_move.empty else 0
        diff = base_freq - target_freq_of_base_move
        assert diff >= DIVERGENCE_THRESHOLD


def test_find_divergence_different_top_moves():
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, 1000), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is not None
        top_base_move = result["base_df"].iloc[0]["Move"]
        top_target_move = result["target_df"].iloc[0]["Move"]
        assert top_base_move == "e2e4"
        assert top_target_move == "g1f3"
        assert result["fen"] == "fake_fen"
        base_moves = result["base_df"]["Move"].tolist()
        target_moves = result["target_df"]["Move"].tolist()
        assert "e2e4" in base_moves
        assert "g1f3" in base_moves
        assert "e2e4" in target_moves
        assert "g1f3" in target_moves


def test_find_divergence_same_top_move():
    # When both ratings yield the same top move, the function should return None
    same_moves = [
        {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
        {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
    ]
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(same_moves, 1000), (same_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None


def test_find_divergence_below_threshold():
    # Using a small epsilon so the frequency difference is just below the threshold.
    epsilon = 0.01
    base_moves = [
        {"uci": "e2e4", "freq": 0.6, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
        {"uci": "g1f3", "freq": 0.3, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
    ]
    target_e2e4_freq = 0.6 - (DIVERGENCE_THRESHOLD - epsilon)
    target_moves = [
        {"uci": "g1f3", "freq": 0.7, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
        {"uci": "e2e4", "freq": target_e2e4_freq, "win_rate": 0.5, "draw_rate": 0.3, "loss_rate": 0.2, "games_total": 1000},
    ]
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(base_moves, 1000), (target_moves, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        # Since the frequency difference is below the threshold, we expect no divergence.
        assert result is None


def test_find_divergence_insufficient_games():
    # Test when there are not enough games for the base rating - should return None
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(DEFAULT_BASE_MOVES, MIN_GAMES - 1), (DEFAULT_TARGET_MOVES, 1000)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None


def test_find_divergence_missing_data():
    # Test when move data is missing for both rating bands - should return None
    with patch("src.divergence.get_move_stats") as mock_stats:
        mock_stats.side_effect = [(None, 0), (None, 0)]
        result = find_divergence("fake_fen", "1400-1600", "1800-2000")
        assert result is None
